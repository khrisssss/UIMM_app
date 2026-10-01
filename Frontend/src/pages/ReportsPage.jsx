import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import AppHeader from "../components/AppHeader";
import api from "../api/api";
import "../App.css";
import "../styles/forms.css";
import "../styles/reports.css";

function ReportsPage() {
  const { companyId } = useParams();

  const [company, setCompany] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);

  const [message, setMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadReportsData() {
    try {
      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const reportsResponse = await api.get(`/companies/${companyId}/reports`);

      if (reportsResponse.data.length > 0) {
        setSelectedReport(reportsResponse.data[0]);
      }
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load reports."));
      console.error(error);
    }
  }

  useEffect(() => {
    loadReportsData();
  }, []);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  useEffect(() => {
    const textareas = document.querySelectorAll(".reports-page-content textarea");

    textareas.forEach((textarea) => {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    });
  }, [selectedReport]);

  function autoResizeTextarea(event) {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  async function generateReportDraft() {
    const confirmed = window.confirm(
      "Generate a new AI report draft? This will replace the current draft report if one already exists."
    );

    if (!confirmed) return;

    try {
      setIsGenerating(true);

      const response = await api.post(
        `/companies/${companyId}/generate-report-draft`
      );

      setSelectedReport(response.data);
      setMessage("AI report draft generated.");

      await loadReportsData();
    } catch (error) {
      setMessage(
        getErrorMessage(
          error,
          "Failed to generate report. Check that company details, answers, scores, and SWOT exist."
        )
      );
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  }

  function updateReportField(field, value) {
    setSelectedReport((previousReport) => ({
      ...previousReport,
      [field]: value,
    }));
  }


  
  async function saveReportEdits(status = "draft") {
    if (!selectedReport) {
      setMessage("No report selected.");
      return;
    }

    try {
      setIsSaving(true);

      const response = await api.patch(
        `/companies/${companyId}/reports/${selectedReport.id}`,
        {
          title: selectedReport.title,
          executive_summary: selectedReport.executive_summary,
          diagnostic_summary: selectedReport.diagnostic_summary,
          swot_summary: selectedReport.swot_summary,
          recommendations: selectedReport.recommendations,
          conclusion: selectedReport.conclusion,
          status: status,
        }
      );

      setSelectedReport(response.data);

      if (status === "validated") {
        setMessage("Report saved and validated.");
      } else {
        setMessage("Report saved as draft.");
      }

      await loadReportsData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to save report."));
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  }

  async function generatePowerPoint() {
    if (!selectedReport) {
      setMessage("No report selected.");
      return;
    }

    if (selectedReport.status !== "validated") {
      setMessage("Save and validate the report before generating PowerPoint.");
      return;
    }

    try {
      setMessage("Generating PowerPoint...");

      const response = await api.post(
        `/companies/${companyId}/reports/${selectedReport.id}/generate-powerpoint`,
        {},
        {
          responseType: "blob",
        }
      );

      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));

      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute(
        "download",
        `rapport_diagnostic_${company?.name || "company"}.pptx`
      );

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(blobUrl);

      setMessage("PowerPoint generated.");
    } catch (error) {
      console.error("PowerPoint error:", error.response?.data || error);
      setMessage("Failed to generate PowerPoint.");
    }
  }

  function goBack() {
    window.location.href = `/companies/${companyId}`;
  }

  return (
    <div className="app-page">
      <AppHeader
        title="Diagnostic report"
        subtitle="Generate, edit, and validate the company report."
      />

      <main className="reports-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="reports-top-actions">
          <button className="secondary-button" onClick={goBack}>
            Back to company
          </button>

          <button
            className="primary-button"
            onClick={generateReportDraft}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating..." : "Generate AI report"}
          </button>
        </section>

        {company && (
          <section className="reports-company-card">
            <div>
              <p className="eyebrow">Company</p>
              <h2>{company.name}</h2>
              <p>
                Status: <strong>{company.status}</strong>
              </p>
            </div>

            <div className="report-status-pill">
              {selectedReport ? selectedReport.status : "No report yet"}
            </div>
          </section>
        )}

        <section className="report-editor-layout">

          <section className="report-editor-card">
            {selectedReport === null ? (
              <div className="empty-card">
                <h3>No report selected</h3>
                <p>
                  Click “Generate AI report” to create the first editable report
                  draft.
                </p>
              </div>
            ) : (
              <>
                <div className="report-editor-header">
                  <div>
                    <p className="eyebrow">Editable report</p>
                    <h2>{selectedReport.title || "Untitled report"}</h2>
                    <p>
                      Source: <strong>{selectedReport.generation_source}</strong>
                      {" "}— Status: <strong>{selectedReport.status}</strong>
                    </p>
                  </div>
                </div>

                <div className="report-form">
                  <div className="form-group">
                    <label>Title</label>
                    <input
                      value={selectedReport.title || ""}
                      onChange={(event) =>
                        updateReportField("title", event.target.value)
                      }
                    />
                  </div>

                  <div className="form-group">
                    <textarea
                      rows="4"
                      value={selectedReport.executive_summary || ""}
                      onInput={autoResizeTextarea}
                      onChange={(event) =>
                        updateReportField(
                          "executive_summary",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Summary</label>
                    <textarea
                      rows="5"
                      value={selectedReport.diagnostic_summary || ""}
                      onInput={autoResizeTextarea}
                      onChange={(event) =>
                        updateReportField(
                          "diagnostic_summary",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>SWOT summary</label>
                    <textarea
                      rows="5"
                      value={selectedReport.swot_summary || ""}
                      onInput={autoResizeTextarea}
                      onChange={(event) =>
                        updateReportField("swot_summary", event.target.value)
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Recommendations</label>
                    <textarea
                      rows="5"
                      value={selectedReport.recommendations || ""}
                      onInput={autoResizeTextarea}
                      onChange={(event) =>
                        updateReportField("recommendations", event.target.value)
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Conclusion</label>
                    <textarea
                      rows="4"
                      value={selectedReport.conclusion || ""}
                      onInput={autoResizeTextarea}
                      onChange={(event) =>
                        updateReportField("conclusion", event.target.value)
                      }
                    />
                  </div>
                </div>

                <div className="report-save-actions">
                  <button
                    className="secondary-button"
                    onClick={() => saveReportEdits("draft")}
                    disabled={isSaving}
                  >
                    {isSaving ? "Saving..." : "Save draft"}
                  </button>

                  <button
                    className="primary-button"
                    onClick={() => saveReportEdits("validated")}
                    disabled={isSaving}
                  >
                    {isSaving ? "Saving..." : "Save and validate"}
                  </button>
                    {selectedReport.status === "validated" && (
                      <button
                        className="primary-button"
                        onClick={generatePowerPoint}
                        disabled={isSaving}
                      >
                        Generate PowerPoint
                      </button>
                    )}
                
                </div>
              </>
            )}
          </section>
        </section>
      </main>
    </div>
  );
}

export default ReportsPage;