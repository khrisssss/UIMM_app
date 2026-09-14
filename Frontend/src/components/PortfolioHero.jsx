import "../styles/portfolio-hero.css";
import logo from "../assets/uimm-logo.jpg";
import bannerImage from "../assets/industry-banner.png";


function PortfolioHero() {
  const user = JSON.parse(localStorage.getItem("user"));

  function goHome() {
    if (user?.role === "admin") {
      window.location.href = "/dashboard";
    } else {
      window.location.href = "/companies";
    }
  }


  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  }

  return (
    <section className="portfolio-hero">
      <nav className="portfolio-navbar">
        <div className="portfolio-brand" onClick={goHome}>
          <img src={logo} alt="UIMM logo" />
          <span>UIMM Boost</span>
        </div>

        <div className="portfolio-nav-links">
          <button type="button" onClick={goHome}>
            Home
          </button>

          <button type="button" className="logout-link" onClick={logout}>
            Logout
          </button>
        </div>
      </nav>

      <div
        className="portfolio-banner"
        style={{ backgroundImage: `url(${bannerImage})` }}
      >
        <div className="portfolio-banner-overlay">
          <h1>Portefeuille des sociétés</h1>
          <span>
            Suivi des entreprises, diagnostics, analyses SWOT et restitutions.
          </span>
        </div>
      </div>
    </section>
  );
}

export default PortfolioHero;