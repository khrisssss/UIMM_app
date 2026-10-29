import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";

import "../App.css";
import "../styles/dashboard.css";

function DashboardPage() {
  const user = JSON.parse(localStorage.getItem("user"));
  const isAdmin = user?.role === "admin";

  const [mlMetrics, setMlMetrics] = useState(null);
  const [useDemoTraining, setUseDemoTraining] = useState(false);
  const [showMlModal, setShowMlModal] = useState(false);
  const [isTrainingModel, setIsTrainingModel] = useState(false);
  const [mlMessage, setMlMessage] = useState("");

  function goTo(path) {
    window.location.href = path;
  }

  useEffect(() => {
    let active = true;
    setMlMetrics(null);
    if (isAdmin) {
      api.get("/ml/model-metrics", { params: { use_demo: useDemoTraining } })
        .then((response) => { if (active) setMlMetrics(response.data); })
        .catch(() => { if (active) setMlMetrics(null); });
    }
    return () => { active = false; };
  }, [isAdmin, useDemoTraining]);

  function downloadEvaluation() {
    const blob = new Blob([JSON.stringify(mlMetrics, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `evaluation-ml-${mlMetrics.is_demo ? "demo" : "reel"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function trainCompanyStateModel() {
    try {
      setIsTrainingModel(true);
      setMlMessage("Entraînement du modèle en cours…");

      const response = await api.post("/ml/train-company-state-model", null, { params: { use_demo: useDemoTraining } });

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
                <span className="card-text">Modifiez le nom et la description des 6 axes.</span>
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

              <label>
                <input
                  type="checkbox"
                  checked={useDemoTraining}
                  disabled={isTrainingModel}
                  onChange={(event) => {
                    setUseDemoTraining(event.target.checked);
                    setMlMetrics(null);
                    setMlMessage("");
                  }}
                />{" "}
                Entraîner uniquement sur les entreprises fictives de démonstration
              </label>
              {useDemoTraining && (
                <p className="page-message">Données fictives : ces résultats servent à tester le fonctionnement. Ils ne mesurent pas la qualité du modèle sur des entreprises réelles. Le modèle de démonstration est enregistré séparément.</p>
              )}

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
                  <span>Entraînement / test</span>
                  <strong>{mlMetrics ? `${mlMetrics.train_size ?? "—"} / ${mlMetrics.test_size ?? "—"}` : "—"}</strong>
                </div>

                <div className="dashboard-ml-detail-row">
                  <span>F1 macro</span>
                  <strong>{mlMetrics?.macro_f1 ?? "—"}</strong>
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

              {mlMetrics?.confusion_matrix && (
                <div style={{ overflowX: "auto" }}>
                  <h3>Matrice de confusion — jeu de test</h3>
                  <table>
                    <caption>Lignes : état observé. Colonnes : état prédit.</caption>
                    <thead><tr>
                      <th scope="col">Observé / Prédit</th>
                      {mlMetrics.confusion_matrix_labels.map((label) => <th scope="col" key={label}>{mlMetrics.labels[label]}</th>)}
                    </tr></thead>
                    <tbody>{mlMetrics.confusion_matrix.map((row, index) => (
                      <tr key={mlMetrics.confusion_matrix_labels[index]}>
                        <th scope="row">{mlMetrics.labels[mlMetrics.confusion_matrix_labels[index]]}</th>
                        {row.map((count, column) => <td key={column}>{count}</td>)}
                      </tr>
                    ))}</tbody>
                  </table>
                  <button type="button" className="secondary-button" onClick={downloadEvaluation}>Télécharger l’évaluation JSON</button>
                </div>
              )}

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

