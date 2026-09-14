import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";

import "../App.css";
import "../styles/dashboard.css";

function DashboardPage() {
  const user = JSON.parse(localStorage.getItem("user"));
  const isAdmin = user?.role === "admin";

  const [mlMetrics, setMlMetrics] = useState(null);
  const [showMlModal, setShowMlModal] = useState(false);
  const [isTrainingModel, setIsTrainingModel] = useState(false);
  const [mlMessage, setMlMessage] = useState("");

  function goTo(path) {
    window.location.href = path;
  }

  async function loadMlMetrics() {
    try {
      const response = await api.get("/ml/model-metrics");
      setMlMetrics(response.data);
    } catch (error) {
      setMlMetrics(null);
    }
  }

  useEffect(() => {
    if (isAdmin) {
      loadMlMetrics();
    }
  }, [isAdmin]);

  async function trainCompanyStateModel() {
    try {
      setIsTrainingModel(true);
      setMlMessage("Training model...");

      const response = await api.post("/ml/train-company-state-model");

      setMlMetrics(response.data.metrics);
      setMlMessage("Model trained successfully.");
    } catch (error) {
      console.error("Train ML model error:", error.response?.data || error);

      setMlMessage(
        error?.response?.data?.detail || "Failed to train the model."
      );
    } finally {
      setIsTrainingModel(false);
    }
  }

  return (
    <div className="app-page">
      <AppHeader
        title="Dashboard"
        subtitle="Select axes, open questionnaires, and follow progress."
      />

      <main className="dashboard-content">
        <section className="hero-card">
          <div>
            <h2>UIMM Boost</h2>
            <p>
              Manage companies, diagnostics, reports, and prediction tools from
              one place.
            </p>
          </div>

          <button
            className="primary-button hero-button"
            onClick={() => goTo("/companies")}
          >
            Open companies
          </button>
        </section>

        <section className="dashboard-grid">
          {isAdmin && (
            <>
              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/axes")}
              >
                <span className="card-title">Diagnostic axes</span>
                <span className="card-text">
                  Edit the name and description of 7 axes.
                </span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/axis-questions")}
              >
                <span className="card-title">Axis questions</span>
                <span className="card-text">
                  Manage categories, diagnostic questions, visibility, and
                  order.
                </span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/profile-questions")}
              >
                <span className="card-title">Company profile</span>
                <span className="card-text">
                  Manage qualitative profile questions for company context.
                </span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/users")}
              >
                <span className="card-title">Users</span>
                <span className="card-text">
                  Create consultants and manage access to the application.
                </span>
              </button>

              <article
                className="dashboard-ml-card"
                onClick={() => {
                  setMlMessage("");
                  setShowMlModal(true);
                }}
              >
                <h3 className="card-title">Company state prediction</h3>

                <p className="dashboard-ml-status">
                  {mlMetrics ? "Ready" : "Not trained yet"}
                </p>

                <p className="card-text dashboard-ml-description">
                  Predicts Bon, À suivre or Attention from diagnostic scores.
                </p>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    setMlMessage("");
                    setShowMlModal(true);
                  }}
                >
                  View details
                </button>
              </article>
            </>
          )}
        </section>

        {showMlModal && (
          <div className="modal-overlay">
            <div className="dashboard-ml-modal">
              <div className="modal-header">
                <div>
                  <h2>Company state prediction</h2>
                  <p>
                    This model predicts the company state using diagnostic
                    scores and company size.
                  </p>
                </div>

                <button
                  type="button"
                  className="modal-close-button"
                  onClick={() => setShowMlModal(false)}
                >
                  ×
                </button>
              </div>

              {mlMessage && <p className="page-message">{mlMessage}</p>}

              <div className="dashboard-ml-details">
                <div className="dashboard-ml-detail-row">
                  <span>Status</span>
                  <strong>{mlMetrics ? "Ready" : "Not trained yet"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Algorithm</span>
                  <strong>
                    {mlMetrics?.algorithm || "RandomForestClassifier"}
                  </strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Dataset size</span>
                  <strong>{mlMetrics?.dataset_size || "—"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Dataset source</span>
                  <strong>{mlMetrics?.dataset_source || "—"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Accuracy</span>
                  <strong>
                    {mlMetrics?.accuracy !== undefined
                      ? `${Math.round(mlMetrics.accuracy * 100)}%`
                      : "—"}
                  </strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Last trained</span>
                  <strong>
                    {mlMetrics?.trained_at
                      ? new Date(mlMetrics.trained_at).toLocaleString()
                      : "—"}
                  </strong>
                </div>
              </div>

              <p className="dashboard-ml-note">
                Training is reserved for administration. Consultants only use
                the prediction result from the Analysis page.
              </p>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowMlModal(false)}
                >
                  Close
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={trainCompanyStateModel}
                  disabled={isTrainingModel}
                >
                  {isTrainingModel ? "Training..." : "Train / Retrain model"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;
