import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CompaniesPage from "./pages/CompaniesPage";
import CompanyDetailsPage from "./pages/CompanyDetailsPage";
import DiagnosticPage from "./pages/DiagnosticPage";
import ScoresPage from "./pages/ScoresPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import AxisQuestionnairePage from "./pages/AxisQuestionnairePage";
import FinancePage from "./pages/FinancePage";
import AdminProfileQuestionsPage from "./pages/AdminProfileQuestionsPage";
import AdminAxisQuestionsPage from "./pages/AdminAxisQuestionsPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AdminAxesPage from "./pages/AdminAxesPage";


function PageBackButton() {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("user"));
  const home = user?.role === "admin" ? "/dashboard" : "/companies";

  if (!token || location.pathname === "/login") return null;

  function goBack() {
    if (window.history.state?.idx > 0) {
      navigate(-1);
      return;
    }
    // Directly opened pages have no previous application history entry.
    const company = location.pathname.match(/^\/companies\/([^/]+)/);
    const fallback = company
      ? (/\/(finance|diagnostic\/[^/]+)$/.test(location.pathname)
          ? `/companies/${company[1]}/diagnostic`
          : "/companies")
      : home;
    if (fallback !== location.pathname) navigate(fallback);
  }

  const atHome = location.pathname === home && !(window.history.state?.idx > 0);
  return (
    <div style={{
      padding: "12px 20px", background: "#072a5f",
      display: "flex", justifyContent: "flex-start",
    }}>
      <button
        type="button"
        className="secondary-button"
        onClick={goBack}
        disabled={atHome}
        aria-label="Retour à la page précédente"
        style={{ opacity: atHome ? 0.5 : 1, cursor: atHome ? "default" : "pointer" }}
      >
        <span aria-hidden="true">← </span>Retour
      </button>
    </div>
  );
}

function App() {
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("user"));
  const isAdmin = user?.role === "admin";

  const [authExpiredMessage, setAuthExpiredMessage] = useState("");

  useEffect(() => {
    function handleAuthExpired(event) {
      setAuthExpiredMessage(
        event.detail?.message ||
          "Votre session a expiré. Veuillez vous reconnecter."
      );
    }

    window.addEventListener("auth-expired", handleAuthExpired);

    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired);
    };
  }, []);

  return (
    <BrowserRouter>
      <PageBackButton />
      <Routes>
        <Route
          path="/login"
          element={token ? <Navigate to="/dashboard" /> : <LoginPage />}
        />

        <Route
          path="/dashboard"
          element={
            token && isAdmin ? (
              <DashboardPage />
            ) : token ? (
              <Navigate to="/companies" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/companies"
          element={token ? <CompaniesPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId"
          element={token ? <CompanyDetailsPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/diagnostic"
          element={token ? <DiagnosticPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/diagnostic/:axisId"
          element={token ? <AxisQuestionnairePage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/finance"
          element={token ? <FinancePage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/scores"
          element={token ? <ScoresPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/analysis"
          element={token ? <AnalysisPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/companies/:companyId/reports"
          element={token ? <ReportsPage /> : <Navigate to="/login" />}
        />

        <Route
          path="/admin/profile-questions"
          element={
            token && isAdmin ? (
              <AdminProfileQuestionsPage />
            ) : token ? (
              <Navigate to="/dashboard" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/admin/axis-questions"
          element={
            token && isAdmin ? (
              <AdminAxisQuestionsPage />
            ) : token ? (
              <Navigate to="/dashboard" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/admin/users"
          element={
            token && isAdmin ? (
              <AdminUsersPage />
            ) : token ? (
              <Navigate to="/dashboard" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/admin/axes"
          element={
            token && isAdmin ? (
              <AdminAxesPage />
            ) : token ? (
              <Navigate to="/dashboard" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="*"
          element={<Navigate to={token ? "/dashboard" : "/login"} />}
        />
      </Routes>

      {authExpiredMessage && (
        <div className="auth-expired-overlay">
          <div className="auth-expired-modal">
            <h2>Session expirée</h2>

            <p>{authExpiredMessage}</p>

            <button
              type="button"
              className="primary-button"
              onClick={() => {
                setAuthExpiredMessage("");
                window.location.href = "/login";
              }}
            >
              Se reconnecter
            </button>
          </div>
        </div>
      )}
    </BrowserRouter>
  );
}

export default App;