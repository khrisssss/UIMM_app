import { displayLabel } from "../utils/french";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import AppHeader from "../components/AppHeader";
import api from "../api/api";
import "../App.css";
import "../styles/forms.css";
import "../styles/reports.css";

const SWOT_CATEGORIES = [
  ["strengths", "Forces"],
  ["weaknesses", "Faiblesses"],
  ["opportunities", "Opportunités"],
  ["threats", "Menaces"],
];

function readAxisAnalysis(value) {
  try {
    const parsed = typeof value === "string" ? JSON.parse(value || "{}") : value;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

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

  async function loadReportRestitution(report) {
    const response = await api.get(
      `/companies/${companyId}/reports/${report.id}/restitution`
    );
    const analysis = {};
    response.data.forEach((axis) => {
      analysis[axis.axis_name] = Object.fromEntries(
        SWOT_CATEGORIES.map(([key]) => [key, axis[key] || []])
      );
    });
    return { ...report, axis_analysis: JSON.stringify(analysis) };
  }

  function updateAxisFinding(axisName, category, value) {
    setSelectedReport((previous) => {
      const analysis = readAxisAnalysis(previous.axis_analysis);
      analysis[axisName] = {
        ...analysis[axisName],
        [category]: value.split("\n"),
      };
      return { ...previous, axis_analysis: JSON.stringify(analysis) };
    });
  }

  async function loadReportsData() {
    try {
      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const reportsResponse = await api.get(`/companies/${companyId}/reports`);

      if (reportsResponse.data.length > 0) {
        setSelectedReport(await loadReportRestitution(reportsResponse.data[0]));
      }
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de charger les rapports."));
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
      "Générer un nouveau brouillon de rapport avec l’IA ? Le brouillon actuel sera remplacé s’il existe déjà."
    );

    if (!confirmed) return;

    try {
      setIsGenerating(true);

      const response = await api.post(
        `/companies/${companyId}/generate-report-draft`
      );

      setSelectedReport(response.data);
      setMessage("Brouillon du rapport généré avec l’IA.");

      await loadReportsData();
    } catch (error) {
      setMessage(
        getErrorMessage(
          error,
          "Impossible de générer le rapport. Vérifiez que la fiche de l’entreprise, les réponses, les scores et le SWOT sont renseignés."
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
      setMessage("Aucun rapport sélectionné.");
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
          axis_analysis: selectedReport.axis_analysis,
          recommendations: selectedReport.recommendations,
          conclusion: selectedReport.conclusion,
          status: status,
        }
      );

      setSelectedReport(response.data);

      if (status === "validated") {
        setMessage("Rapport enregistré et validé.");
      } else {
        setMessage("Rapport enregistré comme brouillon.");
      }

      await loadReportsData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de enregistrer le rapport."));
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  }

  async function generatePowerPoint() {
    if (!selectedReport) {
      setMessage("Aucun rapport sélectionné.");
      return;
    }

    if (selectedReport.status !== "validated") {
      setMessage("Enregistrez et validez le rapport avant de générer le PowerPoint.");
      return;
    }

    try {
      setMessage("Génération du PowerPoint en cours…");

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

      setMessage("PowerPoint généré.");
    } catch (error) {
      console.error("PowerPoint error:", error.response?.data || error);
      setMessage("Impossible de générer le PowerPoint.");
    }
  }

  function goBack() {
    window.location.href = `/companies/${companyId}`;
  }

  return (
    <div className="app-page">
      <AppHeader
        title="Rapport de diagnostic"
        subtitle="Générez, modifiez et validez le rapport de l’entreprise."
      />

      <main className="reports-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="reports-top-actions">
          <button className="secondary-button" onClick={goBack}>Profil</button>

          <button
            className="primary-button"
            onClick={generateReportDraft}
            disabled={isGenerating}
          >
            {isGenerating ? "Génération en cours…" : "Générer le rapport avec l’IA"}
          </button>
        </section>

        {company && (
          <section className="reports-company-card">
            <div>
              <p className="eyebrow">Entreprise</p>
              <h2>{company.name}</h2>
              <p>Statut :<strong>{company.status}</strong>
              </p>
            </div>

            <div className="report-status-pill">
              {selectedReport ? displayLabel(selectedReport.status) : "Aucun rapport pour le moment"}
            </div>
          </section>
        )}

        <section className="report-editor-layout">

          <section className="report-editor-card">
            {selectedReport === null ? (
              <div className="empty-card">
                <h3>Aucun rapport sélectionné</h3>
                <p>Cliquez sur « Générer le rapport avec l’IA » pour créer le premier brouillon modifiable.</p>
              </div>
            ) : (
              <>
                <div className="report-editor-header">
                  <div>
                    <p className="eyebrow">Rapport modifiable</p>
                    <h2>{selectedReport.title || "Rapport sans titre"}</h2>
                    <p>Source :<strong>{displayLabel(selectedReport.generation_source)}</strong>
                      {" "}— Statut : <strong>{displayLabel(selectedReport.status)}</strong>
                    </p>
                  </div>
                </div>

                <div className="report-form">
                  <div className="form-group">
                    <label>Titre</label>
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
                    <label>Synthèse</label>
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

                  <section className="report-restitution" aria-labelledby="restitution-title">
                    <h3 id="restitution-title">Restitution</h3>
                    {Object.entries(readAxisAnalysis(selectedReport.axis_analysis)).length === 0 ? (
                      <p>Aucune analyse par axe disponible. Générez le rapport avec l’IA pour la compléter.</p>
                    ) : (
                      Object.entries(readAxisAnalysis(selectedReport.axis_analysis)).map(([axisName, findings]) => (
                        <section className="report-axis-card" key={axisName}>
                          <h4>{axisName}</h4>
                          <div className="report-axis-swot">
                            {SWOT_CATEGORIES.map(([category, label]) => (
                              <div className="form-group" key={category}>
                                <label>
                                  {label}
                                  <textarea
                                    rows="4"
                                    value={Array.isArray(findings[category])
                                      ? findings[category].join("\n")
                                      : findings[category] || ""}
                                    placeholder="Aucun élément renseigné."
                                    onInput={autoResizeTextarea}
                                    onChange={(event) =>
                                      updateAxisFinding(axisName, category, event.target.value)
                                    }
                                  />
                                </label>
                              </div>
                            ))}
                          </div>
                        </section>
                      ))
                    )}
                  </section>

                  <div className="form-group">
                    <label>Préconisations</label>
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
                    {isSaving ? "Enregistrement en cours…" : "Enregistrer le brouillon"}
                  </button>

                  <button
                    className="primary-button"
                    onClick={() => saveReportEdits("validated")}
                    disabled={isSaving}
                  >
                    {isSaving ? "Enregistrement en cours…" : "Enregistrer et valider"}
                  </button>
                    {selectedReport.status === "validated" && (
                      <button
                        className="primary-button"
                        onClick={generatePowerPoint}
                        disabled={isSaving}
                      >Générer le PowerPoint</button>
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