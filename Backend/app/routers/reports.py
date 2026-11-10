import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.reports import Report
from app.models.user import User
from app.schemas.report import ReportRead, ReportUpdate
from app.services.boost_powerpoint_content_service import build_boost_powerpoint_content
from app.services.report_context import build_report_context
from app.services.report_ai_service import generate_report_draft
from app.dependencies.auth import require_consultant_or_admin

from fastapi.responses import FileResponse
from app.services.powerpoint_report_service import generate_report_powerpoint

router = APIRouter(
    prefix="/companies",
    tags=["Reports"],
)


@router.get("/{company_id}/report-context")
def get_report_context(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Preview the company information, answers, scores, and SWOT used to prepare a report."""
    report_context = build_report_context(company_id=company_id, db=db)

    if report_context is None:
        raise HTTPException(status_code=404, detail="Company not found")

    return report_context


@router.post("/{company_id}/generate-report-draft", response_model=ReportRead)
def create_report_draft(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Generate and save an AI-assisted report draft for the company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    report_context = build_report_context(company_id=company_id, db=db)

    if report_context is None:
        raise HTTPException(status_code=404, detail="Company not found")

    generated_report = generate_report_draft(report_context)
    # Restore the name locally after the anonymized AI request returns.
    generated_report["title"] = f"Rapport de diagnostic — {company.name}"

    existing_report = (
        db.query(Report)
        .filter(
            Report.company_id == company_id,
            Report.status == "draft",
        )
        .first()
    )

    if existing_report is None:
        new_report = Report(
            company_id=company_id,
            title=generated_report["title"],
            executive_summary=generated_report["executive_summary"],
            diagnostic_summary=generated_report["diagnostic_summary"],
            axis_analysis=generated_report["axis_analysis"],
            presentation_content=generated_report["presentation_content"],
            swot_summary=generated_report["swot_summary"],
            recommendations=generated_report["recommendations"],
            conclusion=generated_report["conclusion"],
            generation_source="azure_openai",
            generated_by_ai=True,
            ai_model=os.getenv("AZURE_OPENAI_MODEL", "azure-model"),
            status="draft",
            created_by_user_id=current_user.id,
        )

        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        return new_report

    existing_report.title = generated_report["title"]
    existing_report.executive_summary = generated_report["executive_summary"]
    existing_report.diagnostic_summary = generated_report["diagnostic_summary"]
    existing_report.axis_analysis = generated_report["axis_analysis"]
    existing_report.presentation_content = generated_report["presentation_content"]
    existing_report.swot_summary = generated_report["swot_summary"]
    existing_report.recommendations = generated_report["recommendations"]
    existing_report.conclusion = generated_report["conclusion"]
    existing_report.generation_source = "azure_openai"
    existing_report.generated_by_ai = True
    existing_report.ai_model = os.getenv("AZURE_OPENAI_MODEL", "azure-model")
    existing_report.status = "draft"

    db.commit()
    db.refresh(existing_report)

    return existing_report


@router.get("/{company_id}/reports", response_model=list[ReportRead])
def get_reports_by_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """List the saved reports belonging to this company."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    reports = (
        db.query(Report)
        .filter(Report.company_id == company_id)
        .order_by(Report.created_at.desc())
        .all()
    )

    return reports


@router.patch("/{company_id}/reports/{report_id}", response_model=ReportRead)
def update_report(
    company_id: int,
    report_id: int,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Save report edits. Sending status validated also records the validating user."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    report = (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.company_id == company_id,
        )
        .first()
    )

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    update_data = report_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(report, key, value)

    if report.status == "validated":
        report.validated_by_user_id = current_user.id

    db.commit()
    db.refresh(report)

    return report



@router.get("/{company_id}/reports/{report_id}/restitution")
def get_report_restitution(
    company_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Return the same axis findings used by the PowerPoint restitution."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    report = db.query(Report).filter(
        Report.id == report_id, Report.company_id == company_id
    ).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return build_boost_powerpoint_content(db, company, report)["swot_by_axis"]

# to generate report in powerpoint format
@router.post("/{company_id}/reports/{report_id}/generate-powerpoint")
def generate_report_powerpoint_file(
    company_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_consultant_or_admin),
):
    """Generate a PowerPoint file from the saved report and company data and return it for download."""
    company = db.query(Company).filter(Company.id == company_id).first()

    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    report = (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.company_id == company_id,
        )
        .first()
    )

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "validated":
        raise HTTPException(
            status_code=400,
            detail="The report must be saved and validated before generating a PowerPoint.",
        )

    file_path = generate_report_powerpoint(company=company, report=report, db=db)

    return FileResponse(
        path=file_path,
        filename=file_path.split("/")[-1],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
