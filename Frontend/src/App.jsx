import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CompaniesPage from "./pages/CompaniesPage";
import CompanyDetailsPage from "./pages/CompanyDetailsPage";
import DiagnosticPage from "./pages/DiagnosticPage";
import ScoresPage from "./pages/ScoresPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import AxisQuestionnairePage from "./pages/AxisQuestionnairePage";
import AdminProfileQuestionsPage from "./pages/AdminProfileQuestionsPage";
import AdminAxisQuestionsPage from "./pages/AdminAxisQuestionsPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AdminAxesPage from "./pages/AdminAxesPage";

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