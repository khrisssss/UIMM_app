import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/diagnostic.css";

function DiagnosticPage() {
  const companyId = window.location.pathname.split("/")[2];

  const [company, setCompany] = useState(null);
  const [axesSelection, setAxesSelection] = useState([]);
  const [diagnosticOverview, setDiagnosticOverview] = useState([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadDiagnosticData() {
    try {
      setIsLoading(true);

      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const axesResponse = await api.get(
        `/companies/${companyId}/axes-selection`
      );
      setAxesSelection(axesResponse.data);

      const overviewResponse = await api.get(
        `/companies/${companyId}/diagnostic-overview`
      );
      setDiagnosticOverview(overviewResponse.data);

      // Scores are calculated automatically.
      // The user does not need a separate "Calculer les scores" button.
      await api.post(`/companies/${companyId}/calculate-scores`);
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de charger les données du diagnostic."));
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDiagnosticData();
  }, []);

  async function updateAxisSelection(axisId, isSelected) {
    const previousAxesSelection = axesSelection;
    const previousDiagnosticOverview = diagnosticOverview;

    const updatedAxesSelection = axesSelection.map((axis) =>
      Number(axis.axis_id) === Number(axisId)
        ? {
            ...axis,
            is_selected: isSelected,
          }
        : axis
    );

    const updatedDiagnosticOverview = diagnosticOverview.map((axis) =>
      Number(axis.axis_id) === Number(axisId)
        ? {
            ...axis,
            is_selected: isSelected,
          }
        : axis
    );

    setAxesSelection(updatedAxesSelection);
    setDiagnosticOverview(updatedDiagnosticOverview);

    try {
      await api.patch(`/companies/${companyId}/axes-selection/${axisId}`, {
        is_selected: isSelected,
      });

      setMessage("Sélection des axes mise à jour.");
    } catch (error) {
      setAxesSelection(previousAxesSelection);
      setDiagnosticOverview(previousDiagnosticOverview);
      setMessage("Impossible de mettre à jour la sélection des axes.");
      console.error(error);
    }
  }

  function openQuestionnaire(axis) {
    window.location.href = `/companies/${companyId}/diagnostic/${axis.axis_id}`;
  }

  function openAnalysis() {
    window.location.href = `/companies/${companyId}/analysis`;
  }

  function openReports() {
    window.location.href = `/companies/${companyId}/reports`;
  }

  function openCompanyDetails() {
    window.location.href = `/companies/${companyId}`;
  }

  function getSelectedAxes() {
    return diagnosticOverview.filter((axis) => axis.is_selected);
  }

  function getCompletionClass(percentage) {
    if (percentage >= 100) {
      return "progress-green";
    }

    if (percentage >= 50) {
      return "progress-orange";
    }

    return "progress-red";
  }

  function getCompletionText(answeredQuestions, totalQuestions) {
    if (!totalQuestions || totalQuestions === 0) {
      return "0 % complété";
    }

    const percentage = Math.round((answeredQuestions / totalQuestions) * 100);
    return `${percentage} % complété`;
  }

  function getCompletionPercentage(answeredQuestions, totalQuestions) {
    if (!totalQuestions || totalQuestions === 0) {
      return 0;
    }

    return Math.round((answeredQuestions / totalQuestions) * 100);
  }

  if (isLoading) {
    return (
      <div className="app-page">

        <main className="diagnostic-page-content">
          <p>Chargement…</p>
        </main>
      </div>
    );
  }

  const selectedAxes = getSelectedAxes();

  return (
    <div className="app-page">
      <AppHeader
        title={company ? `${company.name}` : "Diagnostic"}
      />

      <main className="diagnostic-page-content">
        <div className="diagnostic-top-actions">
          <button className="secondary-button" onClick={openCompanyDetails}>Fiche de l’entreprise</button>

          <div className="diagnostic-action-buttons">
            <button className="primary-button" onClick={openAnalysis}>Voir le radar / SWOT</button>

            <button className="secondary-button" onClick={openReports}>Rapport</button>
          </div>
        </div>

        {message && <p className="page-message">{message}</p>}

        <section className="diagnostic-layout">
          <aside className="axis-selection-panel">
            <h2>Sélection des axes</h2>

            <div className="axis-selection-separator"></div>

            <div className="axis-selection-list">
              {axesSelection.map((axis, index) => (
                <label
                  key={axis.axis_id}
                  className={
                    index % 2 === 0
                      ? "axis-selection-row axis-row-light"
                      : "axis-selection-row axis-row-muted"
                  }
                >
                  <input
                    type="checkbox"
                    checked={axis.is_selected}
                    onChange={(event) =>
                      updateAxisSelection(axis.axis_id, event.target.checked)
                    }
                  />

                  <span className="axis-radio-circle"></span>

                  <span className="axis-selection-name">{axis.axis_name}</span>
                </label>
              ))}
            </div>
           </aside>

          <section className="selected-axes-panel">
            {selectedAxes.length === 0 ? (
              <div className="empty-card">
                <h3>Aucun axe sélectionné</h3>
                <p>Sélectionnez au moins un axe de diagnostic à gauche.</p>
              </div>
            ) : (
              <div className="selected-axis-list">
                {selectedAxes.map((axis) => {
                  const completionPercentage = getCompletionPercentage(
                    axis.answered_questions,
                    axis.total_questions
                  );

                  const completionClass =
                    getCompletionClass(completionPercentage);

                  return (
                    <article key={axis.axis_id} className="selected-axis-card">
                      <div className="selected-axis-main">
                        <h3>{axis.axis_name}</h3>

                        <p className="axis-question-count">
                          <strong>{axis.answered_questions}</strong> /{" "}
                          <strong>{axis.total_questions}</strong>questions répondues</p>

                        <p className="axis-completion-text">
                          {getCompletionText(
                            axis.answered_questions,
                            axis.total_questions
                          )}
                        </p>

                        <div className="progress-bar-background">
                          <div
                            className={`progress-bar-fill ${completionClass}`}
                            style={{ width: `${completionPercentage}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="selected-axis-action">
                        <button
                          className="primary-button questionnaire-button"
                          onClick={() => openQuestionnaire(axis)}
                        >
                          Ouvrir le questionnaire
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </section>
      </main>
    </div>
  );
}

export default DiagnosticPage;