"""Idempotent fictional UIMM Boost demo data.

Run inside the backend container: python -m app.seed_demo_companies
Only records with the DEMO prefix are updated on subsequent runs.
"""
from decimal import Decimal

from app.database import SessionLocal
from app.models.company import Company
from app.models.axis import Axis
from app.models.company_axis import CompanyAxis
from app.models.question import Question
from app.models.axis_question_category import AxisQuestionCategory  # register Question.category relationship
from app.models.scoring_scale import ScoringScale
from app.models.scoring_level import ScoringLevel
from app.models.answer import Answer
from app.models.score import Score
from app.models.swot import SWOT
from app.models.financial_year import FinancialYear
from app.routers.scores import calculate_company_scores, question_matches_company_size


# Fully fictional identities and example.com contacts; none represent real companies.
DEMOS = [
    ("Atelier Aurore", "<10", "green", "18 rue des Érables, 31000 Toulouse", "Camille Morel", True, "Recommandation partenaire", 4, 890000),
    ("Mécanique Bellevue", "11-50", "green", "7 avenue du Midi, 31700 Blagnac", "Alex Martin", True, "Salon professionnel", 5, 3500000),
    ("Novacier", ">50", "green", "25 rue des Tilleuls, 31670 Labège", "Nora Petit", True, "Réseau UIMM", 6, 7800000),
    ("Usinage Horizon", "<10", "orange", "4 rue des Forges, 31100 Toulouse", "Samir Laurent", False, "Autre", 7, 610000),
    ("Thermo Delta", "11-50", "orange", "12 allée des Ateliers, 31270 Cugnaux", "Léa Garnier", True, "Recommandation partenaire", 8, 2200000),
    ("Composites Lune", ">50", "orange", "9 avenue des Métiers, 31600 Muret", "Noé Bernard", False, "Autre", 9, 5100000),
    ("Métal Rivage", "<10", "red", "3 rue du Pont, 31300 Toulouse", "Inès Robert", False, "Salon professionnel", 10, 420000),
    ("Précision Azur", "11-50", "red", "14 chemin des Pins, 31120 Portet-sur-Garonne", "Hugo Faure", False, "Autre", 11, 1300000),
    ("Forge Sillage", ">50", "red", "6 rue des Arts, 31830 Plaisance-du-Touch", "Emma Vidal", False, "Réseau UIMM", 12, 3900000),
    ("Industrie Élan", "11-50", "orange", "17 avenue du Parc, 31170 Tournefeuille", "Maya Dubois", True, "Autre", 13, 2700000),
]

SWOT = {
    "green": (
        ["Processus de production suivis", "Objectifs partagés avec les équipes"],
        ["Certaines données restent dispersées"],
        ["Développer un nouveau segment industriel"],
        ["Hausse du coût des matières premières"],
    ),
    "orange": (
        ["Savoir-faire technique reconnu"],
        ["Pilotage commercial et RH encore partiel", "Dépendance à quelques personnes clés"],
        ["Structurer le suivi des indicateurs et la prospection"],
        ["Concurrence sur les prix et délais"],
    ),
    "red": (
        ["Équipe expérimentée sur son métier"],
        ["Processus peu formalisés", "Suivi financier irrégulier"],
        ["Mettre en place un plan d'amélioration opérationnelle"],
        ["Perte possible de clients majeurs"],
    ),
}


def upsert(db, model, filters, values):
    row = db.query(model).filter_by(**filters).first()
    if row is None:
        row = model(**filters)
        db.add(row)
    for key, value in values.items():
        setattr(row, key, value)
    db.flush()
    return row


def financial_values(revenue, state, year, kind):
    factor = {"green": Decimal("0.13"), "orange": Decimal("0.075"), "red": Decimal("0.025")}[state]
    amount = Decimal(revenue) * (Decimal("0.92") if year == 2024 else Decimal("1") if year == 2025 else Decimal("1.04"))
    cash = amount * factor
    return {
        "revenue": amount.quantize(Decimal("0.01")),
        "ebitda": cash.quantize(Decimal("0.01")),
        "depreciation": (amount * Decimal("0.02")).quantize(Decimal("0.01")),
        "operating_result": (cash - amount * Decimal("0.02")).quantize(Decimal("0.01")),
        "net_result": (cash - amount * Decimal("0.04")).quantize(Decimal("0.01")),
        "cash_flow": (cash - amount * Decimal("0.01")).quantize(Decimal("0.01")),
        "equity": (amount * Decimal("0.35")).quantize(Decimal("0.01")),
        "gross_debt": (amount * Decimal("0.22")).quantize(Decimal("0.01")),
        "gross_cash": (amount * Decimal("0.09")).quantize(Decimal("0.01")),
        "factoring": Decimal("0"),
        "total_assets": (amount * Decimal("0.8")).quantize(Decimal("0.01")),
        "capex": (amount * Decimal("0.06")).quantize(Decimal("0.01")),
        "debt_repayments": (amount * Decimal("0.035")).quantize(Decimal("0.01")),
        "notes": "Données fictives de démonstration. Hypothèses simplifiées." if kind == "forecast" else "Données fictives de démonstration.",
    }


def seed():
    db = SessionLocal()
    try:
        axes = db.query(Axis).filter(Axis.is_active == True).order_by(Axis.order_index).all()
        if not axes:
            raise RuntimeError("No axes found. Seed axes and scoring scales first.")
        questions = db.query(Question).filter(Question.is_active == True).order_by(Question.axis_id, Question.order_index).all()
        if not questions:
            raise RuntimeError("No active questions found. Add the diagnostic questions first.")
        scales = {s.axis_id: s for s in db.query(ScoringScale).filter(ScoringScale.is_active == True).all()}
        levels = {s.axis_id: sorted(db.query(ScoringLevel).filter_by(scoring_scale_id=s.id).all(), key=lambda level: level.score_value if level.score_value is not None else -1) for s in scales.values()}
        for axis in axes:
            if any(q.axis_id == axis.id for q in questions) and not [l for l in levels.get(axis.id, []) if l.score_value is not None and l.score_value > 0]:
                raise RuntimeError(f"Missing usable scoring levels for {axis.name}")

        for name, size, state, address, contact, has_rse, origin, index, revenue in DEMOS:
            demo_name = f"DEMO — {name}"
            company = upsert(db, Company, {"name": demo_name}, {
                "company_size": size, "address": address, "contact_name": contact,
                "contact_email": f"demo{index}@example.com", "contact_phone": f"+33 5 61 00 00 {index:02d}",
                "status": "Client" if index != 13 else "Prospect", "is_archived": index != 13,
                "prediag_origin": origin, "prediag_origin_other": "Contact lors d'une rencontre régionale" if origin == "Autre" else None,
                "has_rse": has_rse, "specific_regulatory_constraints": "Exigences qualité et traçabilité des lots; revue documentaire annuelle.",
                "general_comment": "Entreprise fictive créée pour tester le diagnostic et le modèle ML.",
                "general_state": state,
            })
            for axis in axes:
                upsert(db, CompanyAxis, {"company_id": company.id, "axis_id": axis.id}, {"is_selected": True})
            for question in questions:
                if not question_matches_company_size(question, size):
                    continue
                candidates = [l for l in levels.get(question.axis_id, []) if l.score_value is not None and 1 <= l.score_value <= (question.max_score or 5)]
                if not candidates:
                    continue
                # Rotate within each state so scores are plausible rather than uniform.
                if state == "red":
                    level = candidates[min((question.order_index + index) % 2, len(candidates) - 1)]
                else:
                    target = len(candidates) - (1 if state == "green" else 3)
                    level = candidates[max(0, min(len(candidates) - 1, target + ((question.order_index + index) % 2)))]
                upsert(db, Answer, {"company_id": company.id, "question_id": question.id}, {
                    "score_code": level.code, "score_value": level.score_value,
                    "answer_text": None,
                    "comment": f"Exemple fictif : {level.label.lower()}. Point vérifié pendant le diagnostic.",
                })
            strengths, weaknesses, opportunities, threats = SWOT[state]
            upsert(db, SWOT, {"company_id": company.id, "axis_id": None}, {
                "strengths": "\n".join(f"- {item}" for item in strengths),
                "weaknesses": "\n".join(f"- {item}" for item in weaknesses),
                "opportunities": "\n".join(f"- {item}" for item in opportunities),
                "threats": "\n".join(f"- {item}" for item in threats),
                "status": "validated", "generation_source": "demo_seed", "generated_by_ai": False,
            })
            for year, kind in [(2024, "actual"), (2025, "actual"), (2026, "forecast")]:
                upsert(db, FinancialYear, {"company_id": company.id, "year": year, "kind": kind}, financial_values(revenue, state, year, kind))
            db.flush()
            calculate_company_scores(company.id, db)
            print(f"{demo_name}: {state}, {'archived' if company.is_archived else 'active'}")
        db.commit()
        print("10 fictional companies seeded. Run again to refresh only DEMO records.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
