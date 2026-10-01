import { useLocation, useNavigate } from "react-router-dom";

function PageBackButton() {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");
  const user = JSON.parse(localStorage.getItem("user"));
  const home = user?.role === "admin" ? "/dashboard" : "/companies";

  const consultantHome = user?.role === "consultant" && /^\/companies\/?$/.test(location.pathname);

  if (consultantHome || !token || location.pathname === "/login" || location.pathname === "/dashboard" || /\/analysis\/?$/.test(location.pathname)) return null;

  function goBack() {
    const report = location.pathname.match(/^\/companies\/([^/]+)\/reports\/?$/);
    if (report) {
      navigate(`/companies/${report[1]}/analysis`);
      return;
    }
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
      padding: "12px 20px", background: "#ebe8e9",
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

export default PageBackButton;
