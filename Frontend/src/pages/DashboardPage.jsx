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
      setMlMessage("Entraînement du modèle en cours…");

      const response = await api.post("/ml/train-company-state-model");

      setMlMetrics(response.data.metrics);
      setMlMessage("Modèle entraîné avec succès.");
    } catch (error) {
      console.error("Train ML model error:", error.response?.data || error);

      setMlMessage(
        error?.response?.data?.detail || "Impossible de entraîner le modèle."
      );
    } finally {
      setIsTrainingModel(false);
    }
  }

  return (
    <div className="app-page">
      <AppHeader
        title="Tableau de bord"
        subtitle="Sélectionnez les axes, ouvrez les questionnaires et suivez leur progression."
      />

      <main className="dashboard-content">
        <section className="hero-card">
          <div>
            <h2>UIMM Boost</h2>
            <p>Gérez les entreprises, les diagnostics, les rapports et les outils de prédiction depuis un seul espace.</p>
          </div>

          <button
            className="primary-button hero-button"
            onClick={() => goTo("/companies")}
          >Voir les entreprises</button>
        </section>

        <section className="dashboard-grid">
          {isAdmin && (
            <>
              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/axes")}
              >
                <span className="card-title">Axes de diagnostic</span>
                <span className="card-text">Modifiez le nom et la description des 7 axes.</span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/axis-questions")}
              >
                <span className="card-title">Questions par axe</span>
                <span className="card-text">Gérez les catégories, les questions de diagnostic, leur visibilité et leur ordre.</span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/profile-questions")}
              >
                <span className="card-title">Profil de l’entreprise</span>
                <span className="card-text">Gérez les questions qualitatives pour préciser le contexte de l’entreprise.</span>
              </button>

              <button
                className="dashboard-card"
                onClick={() => goTo("/admin/users")}
              >
                <span className="card-title">Utilisateurs</span>
                <span className="card-text">Créez des comptes consultants et gérez les accès à l’application.</span>
              </button>

              <article
                className="dashboard-ml-card"
                onClick={() => {
                  setMlMessage("");
                  setShowMlModal(true);
                }}
              >
                <h3 className="card-title">Prédiction de l’état de l’entreprise</h3>

                <p className="dashboard-ml-status">
                  {mlMetrics ? "Prêt" : "Pas encore entraîné"}
                </p>

                <p className="card-text dashboard-ml-description">Prédit l’état Bon, À suivre ou Attention à partir des scores du diagnostic.</p>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    setMlMessage("");
                    setShowMlModal(true);
                  }}
                >Voir les détails</button>
              </article>
            </>
          )}
        </section>

        {showMlModal && (
          <div className="modal-overlay">
            <div className="dashboard-ml-modal">
              <div className="modal-header">
                <div>
                  <h2>Prédiction de l’état de l’entreprise</h2>
                  <p>Ce modèle prédit l’état de l’entreprise à partir des scores du diagnostic et de sa taille.</p>
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
                  <span>Statut</span>
                  <strong>{mlMetrics ? "Prêt" : "Pas encore entraîné"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Algorithme</span>
                  <strong>
                    {mlMetrics?.algorithm || "RandomForestClassifier"}
                  </strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Nombre de données</span>
                  <strong>{mlMetrics?.dataset_size || "—"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Source des données</span>
                  <strong>{mlMetrics?.dataset_source || "—"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Taux de bonnes prédictions</span>
                  <strong>
                    {mlMetrics?.accuracy !== undefined
                      ? `${Math.round(mlMetrics.accuracy * 100)}%`
                      : "—"}
                  </strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>Dernier entraînement</span>
                  <strong>
                    {mlMetrics?.trained_at
                      ? new Date(mlMetrics.trained_at).toLocaleString("fr-FR")
                      : "—"}
                  </strong>
                </div>
              </div>

              <p className="dashboard-ml-note">L’entraînement est réservé à l’administration. Les consultants consultent le résultat de la prédiction sur la page Analyse.</p>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowMlModal(false)}
                >Fermer</button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={trainCompanyStateModel}
                  disabled={isTrainingModel}
                >
                  {isTrainingModel ? "Entraînement en cours…" : "Entraîner / Réentraîner le modèle"}
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
