import AppHeader from "../components/AppHeader";

import "../App.css";
import "../styles/dashboard.css";

function DashboardPage() {
  const user = JSON.parse(localStorage.getItem("user"));
  const isAdmin = user?.role === "admin";

  function goTo(path) {
    window.location.href = path;
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
            <p>Gérez les entreprises, les diagnostics et les rapports depuis un seul espace.</p>
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
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default DashboardPage;


