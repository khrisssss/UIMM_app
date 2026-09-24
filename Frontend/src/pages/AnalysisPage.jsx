import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/analysis.css";

function getErrorMessage(error, fallbackMessage) {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallbackMessage;
}

function normalizeSwotValue(value) {
  if (!value) return "";

  if (Array.isArray(value)) return value.join("\n");

  const textValue = String(value).trim();

  if (textValue === "{}") return "";

  if (textValue.startsWith("{") && textValue.endsWith("}")) {
    const withoutBraces = textValue.slice(1, -1).trim();

    if (!withoutBraces) return "";

    return withoutBraces
      .split('","')
      .map((item) => item.replace(/^"/, "").replace(/"$/, "").trim())
      .filter((item) => item !== "")
      .join("\n");
  }

  return textValue;
}

function AnalysisPage() {
  const { companyId } = useParams();
  const scoreDetailsModalRef = useRef(null);

  const [company, setCompany] = useState(null);
  const [scores, setScores] = useState([]);
  const [archiveAverageScores, setArchiveAverageScores] = useState([]);
  const [axes, setAxes] = useState([]);
  const [swot, setSwot] = useState(null);

  const [swotForm, setSwotForm] = useState({
    strengths: "",
    weaknesses: "",
    opportunities: "",
    threats: "",
  });

  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showScoreDetailsModal, setShowScoreDetailsModal] = useState(false);

  // for the ml 
  const [mlPrediction, setMlPrediction] = useState(null);
  const [isPredictingState, setIsPredictingState] = useState(false);
  const [isApplyingPrediction, setIsApplyingPrediction] = useState(false);
  const [showMlPredictionModal, setShowMlPredictionModal] = useState(false);

  const fillSwotForm = useCallback((swotData) => {
    if (!swotData) {
      setSwotForm({
        strengths: "",
        weaknesses: "",
        opportunities: "",
        threats: "",
      });
      return;
    }

    setSwotForm({
      strengths: normalizeSwotValue(swotData.strengths),
      weaknesses: normalizeSwotValue(swotData.weaknesses),
      opportunities: normalizeSwotValue(swotData.opportunities),
      threats: normalizeSwotValue(swotData.threats),
    });
  }, []);

  function getAxisName(score) {
    if (score.axis_name) return score.axis_name;
    if (score.axis?.name) return score.axis.name;

    const foundAxis = axes.find(
      (axisItem) => Number(axisItem.id) === Number(score.axis_id)
    );

    return foundAxis ? foundAxis.name : `Axis ${score.axis_id}`;
  }

  function getScorePercentage(score) {
    return Number(score.score_percentage ?? score.percentage ?? 0);
  }

  function getArchiveAverageForAxis(axisId) {
    const foundAverage = archiveAverageScores.find(
      (averageItem) => Number(averageItem.axis_id) === Number(axisId)
    );

    if (!foundAverage) return null;

    return Number(foundAverage.archive_average_percentage ?? 0);
  }

  // Each radar point joins this company's axis percentage to its archive average.
  // null means there is no archived comparison for that axis yet.
  function getRadarData() {
    return scores.map((score) => ({
      axis: getAxisName(score),
      score: getScorePercentage(score),
      archiveAverage: getArchiveAverageForAxis(score.axis_id),
    }));
  }

  function getAverageScore() {
    if (scores.length === 0) return 0;

    const total = scores.reduce(
      (sum, score) => sum + Number(getScorePercentage(score)),
      0
    );

    return Math.round(total / scores.length);
  }

  // This is the mean of the available per-axis archive averages, not a
  // percentage pooled over every archived answer.
  function getArchiveGlobalAverage() {
    if (archiveAverageScores.length === 0) return null;

    const total = archiveAverageScores.reduce(
      (sum, averageItem) =>
        sum + Number(averageItem.archive_average_percentage ?? 0),
      0
    );

    return Math.round(total / archiveAverageScores.length);
  }

  function autoResizeTextarea(event) {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  const loadAnalysisData = useCallback(async () => {
    try {
      setIsLoading(true);
      setMlPrediction(null);

      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const axesResponse = await api.get("/axes/");
      setAxes(axesResponse.data);

      // Refresh the saved scores before loading the radar and archive comparison.
      await api.post(`/companies/${companyId}/calculate-scores`);

      const scoresResponse = await api.get(`/companies/${companyId}/scores`);
      setScores(scoresResponse.data);

      try {
        const archiveAverageResponse = await api.get(
          `/companies/${companyId}/scores/archive-average`
        );
        setArchiveAverageScores(archiveAverageResponse.data);
      } catch (error) {
        console.warn("No archive average scores found yet.", error);
        setArchiveAverageScores([]);
      }

      try {
        const swotResponse = await api.get(`/companies/${companyId}/swot`);
        const swots = swotResponse.data;

        const companySwot = Array.isArray(swots)
          ? swots.find((item) => item.axis_id === null)
          : null;
        if (companySwot) {
          const latestSwot = companySwot;
          setSwot(latestSwot);
          fillSwotForm(latestSwot);
        } else {
          setSwot(null);
          fillSwotForm(null);
        }
      } catch (error) {
        console.warn("No SWOT found yet.", error);
        setSwot(null);
        fillSwotForm(null);
      }
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load analysis data."));
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, [companyId, fillSwotForm]);

  useEffect(() => {
    loadAnalysisData();
  }, [loadAnalysisData]);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  useEffect(() => {
    function resizeSwotTextareas() {
      const textareas = document.querySelectorAll(".swot-grid textarea");

      textareas.forEach((textarea) => {
        textarea.style.height = "auto";
        textarea.style.height = `${textarea.scrollHeight}px`;
      });
    }

    resizeSwotTextareas();

    const timer = setTimeout(() => {
      resizeSwotTextareas();
    }, 100);

    return () => clearTimeout(timer);
  }, [swotForm]);

  useEffect(() => {
    if (!showScoreDetailsModal) return;

    const previousFocus = document.activeElement;
    const modal = scoreDetailsModalRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    modal.focus();

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        setShowScoreDetailsModal(false);
      }
      if (event.key === "Tab") {
        const buttons = modal.querySelectorAll("button:not(:disabled)");
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === modal)) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === modal)) {
          event.preventDefault();
          first?.focus();
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [showScoreDetailsModal]);

  function updateSwotField(field, value) {
    setSwotForm((previousForm) => ({
      ...previousForm,
      [field]: value,
    }));
  }

  async function predictGeneralState() {
    try {
      setIsPredictingState(true);
      setMessage("Predicting company state...");

      const response = await api.post(`/companies/${companyId}/predict-state`);

      setMlPrediction(response.data);
      setShowMlPredictionModal(true);
      setMessage("");
    } catch (error) {
      console.error("ML prediction error:", error.response?.data || error);
      setMessage(getErrorMessage(error, "Failed to predict company state."));
    } finally {
      setIsPredictingState(false);
    }
  }

  async function applyMlPredictionToCompanyState() {
    if (!mlPrediction || isPredictingState || isApplyingPrediction) return;

    try {
      setIsApplyingPrediction(true);
      const response = await api.patch(`/companies/${companyId}`, {
        general_state: mlPrediction.predicted_state,
      });
      setCompany(response.data);
      setMessage("Prediction applied to company state.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to apply prediction."));
    } finally {
      setIsApplyingPrediction(false);
    }
  }

  async function generateSwot() {
    if (isGenerating || isSaving) return;
    try {
      setIsGenerating(true);
      setMessage("Generating SWOT...");

      const response = await api.post(`/companies/${companyId}/generate-swot`);

      setSwot(response.data);
      fillSwotForm(response.data);

      setMessage("SWOT generated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to generate SWOT."));
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  }

  async function saveSwot() {
    if (isGenerating || isSaving) return;

    try {
      setIsSaving(true);

      const payload = {
        strengths: swotForm.strengths,
        weaknesses: swotForm.weaknesses,
        opportunities: swotForm.opportunities,
        threats: swotForm.threats,
        status: "validated",
      };

      const response = swot
        ? await api.patch(`/companies/${companyId}/swot/${swot.id}`, payload)
        : await api.post(`/companies/${companyId}/swot`, {
            ...payload,
            axis_id: null,
            generation_source: "manual",
            generated_by_ai: false,
          });

      setSwot(response.data);
      fillSwotForm(response.data);

      setMessage("SWOT saved and validated.");
    } catch (error) {
      console.error("SWOT save error:", error.response?.data || error);
      setMessage(getErrorMessage(error, "Failed to save SWOT."));
    } finally {
      setIsSaving(false);
    }
  }

  function openDiagnosticOverview() {
    window.location.href = `/companies/${companyId}/diagnostic`;
  }

  function openReport() {
    window.location.href = `/companies/${companyId}/reports`;
  }

  if (isLoading) {
    return (
      <div className="app-page">
        <main className="analysis-page-content">
          <p>Loading analysis...</p>
        </main>
      </div>
    );
  }

  const radarData = getRadarData();
  const averageScore = getAverageScore();
  const archiveGlobalAverage = getArchiveGlobalAverage();

  return (
    <div className="app-page">
      <AppHeader
        title={company ? company.name : "Radar / SWOT"}
        subtitle="Radar chart, archive average, and SWOT analysis."
      />

      <main className="analysis-page-content">
        <div className="analysis-top-actions">
          <button className="secondary-button" onClick={openDiagnosticOverview}>
            Back to diagnostic
          </button>

          <button className="primary-button" onClick={openReport}>
            Continue to report
          </button>
        </div>

        {message && <div className="toast-message" role="status">{message}</div>}

        <section className="analysis-top-grid">
          <div className="analysis-card">
            {radarData.length === 0 ? (
              <div className="empty-card">
                <h3>No scores yet</h3>
                <p>Complete questionnaires first.</p>
              </div>
            ) : (
              <>
                <div className="radar-chart-box">
                  <ResponsiveContainer width="100%" height={430}>
                    <RadarChart
                      data={radarData}
                      cx="50%"
                      cy="50%"
                      outerRadius="68%"
                      margin={{ top: 40, right: 90, bottom: 40, left: 90 }}
                    >
                      <PolarGrid stroke="#cbd5e1" />

                      <PolarAngleAxis
                        dataKey="axis"
                        tick={{
                          fill: "#0f172a",
                          fontSize: 13,
                          fontWeight: 700,
                        }}
                      />

                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{
                          fill: "#64748b",
                          fontSize: 12,
                        }}
                        tickCount={5}
                      />

                      <Radar
                        name="Entreprise actuelle"
                        dataKey="score"
                        stroke="#16a34a"
                        strokeWidth={2}
                        fill="#22c55e"
                        fillOpacity={0.25}
                        dot={{
                          r: 4,
                          fill: "#166534",
                        }}
                      />

                      <Radar
                        name="Moyenne archive"
                        dataKey="archiveAverage"
                        stroke="#2563eb"
                        strokeWidth={2}
                        fill="#2563eb"
                        fillOpacity={0.05}
                        dot={{
                          r: 4,
                          fill: "#1d4ed8",
                        }}
                      />

                      <Tooltip
                        formatter={(value, name) => {
                          if (value === null || value === undefined) {
                            return ["No archive data", name];
                          }

                          return [`${value}%`, name];
                        }}
                        labelFormatter={(label) => `Axe : ${label}`}
                      />

                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                

                <div className="radar-action-buttons">
                  <button
                    className="secondary-button"
                    onClick={() => setShowScoreDetailsModal(true)}
                  >
                    Voir le détail du calcul
                  </button>

                  <button
                    className="primary-button"
                    onClick={predictGeneralState}
                    disabled={isPredictingState}
                  >
                    {isPredictingState ? "Predicting..." : "Predict state"}
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        
        <section className="analysis-card swot-section">
          <div className="analysis-card-header">
            <div>
              <p className="eyebrow">SWOT</p>
            </div>

            <button
              className="secondary-button"
              onClick={generateSwot}
              disabled={isGenerating || isSaving}
            >
              {isGenerating ? "Generating..." : "Generate SWOT"}
            </button>
          </div>

          <div className="swot-grid">
            <div className="swot-center" aria-hidden="true">
              <span>S</span><span>W</span><span>O</span><span>T</span>
            </div>
            <div className="form-group swot-card swot-card-strengths">
              <label htmlFor="swot-strengths">Strengths</label>
              <textarea
                id="swot-strengths"
                disabled={isGenerating || isSaving}
                rows="3"
                value={swotForm.strengths}
                onInput={autoResizeTextarea}
                onChange={(event) =>
                  updateSwotField("strengths", event.target.value)
                }
                placeholder="Add strengths..."
              />
            </div>

            <div className="form-group swot-card swot-card-weaknesses">
              <label htmlFor="swot-weaknesses">Weaknesses</label>
              <textarea
                id="swot-weaknesses"
                disabled={isGenerating || isSaving}
                rows="3"
                value={swotForm.weaknesses}
                onInput={autoResizeTextarea}
                onChange={(event) =>
                  updateSwotField("weaknesses", event.target.value)
                }
                placeholder="Add weaknesses..."
              />
            </div>

            <div className="form-group swot-card swot-card-opportunities">
              <label htmlFor="swot-opportunities">Opportunities</label>
              <textarea
                id="swot-opportunities"
                disabled={isGenerating || isSaving}
                rows="3"
                value={swotForm.opportunities}
                onInput={autoResizeTextarea}
                onChange={(event) =>
                  updateSwotField("opportunities", event.target.value)
                }
                placeholder="Add opportunities..."
              />
            </div>

            <div className="form-group swot-card swot-card-threats">
              <label htmlFor="swot-threats">Threats</label>
              <textarea
                id="swot-threats"
                disabled={isGenerating || isSaving}
                rows="3"
                value={swotForm.threats}
                onInput={autoResizeTextarea}
                onChange={(event) =>
                  updateSwotField("threats", event.target.value)
                }
                placeholder="Add threats..."
              />
            </div>
          </div>

          <div className="swot-actions">
            <button
              className="primary-button"
              onClick={saveSwot}
              disabled={!company || isSaving || isGenerating}
            >
              {isSaving ? "Saving..." : "Save SWOT"}
            </button>

            <button className="secondary-button" onClick={openReport}>
              Continue to report
            </button>
          </div>
        </section>
      </main>
      {showMlPredictionModal && mlPrediction && (
        <div className="modal-overlay">
          <div className="ml-prediction-modal">
            <div className="modal-header">
              <div>
                <h2>Company state prediction</h2>
                <p>Based on diagnostic scores and company size.</p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={() => setShowMlPredictionModal(false)}
              >
                ×
              </button>
            </div>

            <div className="ml-prediction-main-result">
              <p className="ml-prediction-label">Predicted state</p>

              <h3
                className={
                  mlPrediction.predicted_state === "green"
                    ? "prediction-green"
                    : mlPrediction.predicted_state === "red"
                    ? "prediction-red"
                    : "prediction-orange"
                }
              >
                {mlPrediction.predicted_state_label}
              </h3>

              <p className="ml-confidence">
                Confidence: {Math.round(mlPrediction.confidence * 100)}%
              </p>
            </div>

            <div className="ml-probability-list">
              {Object.entries(mlPrediction.probabilities || {}).map(
                ([state, value]) => (
                  <div key={state} className="ml-probability-row">
                    <span>{value.label}</span>
                    <strong>{Math.round(value.probability * 100)}%</strong>
                  </div>
                )
              )}
            </div>

            <p className="ml-warning-text">
              This is a decision-support prediction. The consultant remains
              responsible for validating the final company state.
            </p>

            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={() => setShowMlPredictionModal(false)}
              >
                Close
              </button>

              <button
                className="primary-button"
                onClick={applyMlPredictionToCompanyState}
                disabled={isApplyingPrediction}
              >
                {isApplyingPrediction
                  ? "Applying..."
                  : "Apply prediction to company state"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showScoreDetailsModal && (
        <div className="modal-overlay">
          <div
            className="score-details-modal"
            ref={scoreDetailsModalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="score-details-title"
            tabIndex={-1}
          >
            <div className="score-details-modal-header">
              <div>
                <h2 id="score-details-title">Détail du calcul des scores</h2>
                <p>
                  <span className="calculation-info-icon">ℹ️</span>
                  Le pourcentage est calculé avec la formule : score obtenu ÷
                  score maximum × 100.
                </p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                aria-label="Close score details"
                onClick={() => setShowScoreDetailsModal(false)}
              >
                ×
              </button>
            </div>

            <div className="calculation-help-box">
              <strong>Comment lire ces résultats ?</strong>
              <p>
                Le score de l’entreprise est calculé pour chaque axe
                sélectionné. La moyenne archive correspond à la moyenne des
                scores des entreprises archivées dans la base de données, pour
                les mêmes axes.
              </p>
            </div>

            <div className="modal-average-row">
              <article className="modal-average-card">
                <span>Average company score</span>
                <strong>{averageScore}%</strong>
                <p>
                  This is the average score of the current company across the selected
                  diagnostic axes.
                </p>
              </article>

              <article className="modal-average-card">
                <span>Archive average</span>
                <strong>
                  {archiveGlobalAverage === null
                    ? "No archive yet"
                    : `${archiveGlobalAverage}%`}
                </strong>
                <p>
                  This is the average score from the archived companies in your database.
                </p>
              </article>
            </div>

            <div className="score-details-modal-list">
              {scores.map((score, index) => {
                const archiveAverage = getArchiveAverageForAxis(score.axis_id);
                const currentPercentage = getScorePercentage(score);
                const difference =
                  archiveAverage === null
                    ? null
                    : Math.round(currentPercentage - archiveAverage);

                return (
                  <article
                    key={`${score.id || score.axis_id}-${index}`}
                    className="score-details-modal-card"
                  >
                    <h3>{getAxisName(score)}</h3>

                    <div className="score-detail-line">
                      <span>Score obtenu</span>
                      <strong>
                        {score.score_total ?? score.total_score ?? "—"} /{" "}
                        {score.score_max ?? score.max_score ?? "—"}
                      </strong>
                    </div>

                    <div className="score-detail-line">
                      <span>Pourcentage actuel</span>
                      <strong>{currentPercentage}%</strong>
                    </div>

                    <div className="score-detail-line">
                      <span>Moyenne archive</span>
                      <strong>
                        {archiveAverage === null
                          ? "Aucune archive"
                          : `${archiveAverage}%`}
                      </strong>
                    </div>

                    <div className="score-detail-line">
                      <span>Écart avec la moyenne archive</span>
                      <strong>
                        {difference === null
                          ? "—"
                          : difference > 0
                          ? `+${difference}%`
                          : `${difference}%`}
                      </strong>
                    </div>

                    <div className="score-detail-line">
                      <span>Questions répondues</span>
                      <strong>{score.answered_questions ?? "—"}</strong>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnalysisPage;
