import "../App.css";

function AppHeader({ title, subtitle }) {
  const user = JSON.parse(localStorage.getItem("user"));

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }

  function goHome() {
    if (user?.role === "admin") {
      window.location.href = "/dashboard";
    } else {
      window.location.href = "/companies";
    }
  }

  return (
    <header className="top-app-header">
      <div>
        <p className="eyebrow">UIMM Boost</p>
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>

      <div className="top-header-actions">
        <button className="secondary-button" onClick={goHome}>
          Home
        </button>

        <div className="user-panel compact">
          <div>
            <p className="user-name">{user?.full_name || "User"}</p>
            <p className="user-role">{user?.role || "consultant"}</p>
          </div>

          <button className="secondary-button" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default AppHeader;