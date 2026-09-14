import { useEffect, useMemo, useState } from "react";

import api from "../api/api";

import "../App.css";
import "../styles/forms.css";
import "../styles/companies.css";
import "../styles/modals.css";

import PortfolioHero from "../components/PortfolioHero";

const COMPANY_STATUSES = [
  "Prospect",
  "Prédiag réalisé",
  "Diag en cours",
  "Diag finalisé",
  "Mission Compl en cours",
  "MC finalisée",
  "Finalisé",
];

const DIAG_SATISFACTION_SURVEY_LINK =
  "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=8EL7gvyBgEGl4zgLvuWNvW8FQay4Rh1FhDFQxNBKaNtUNTZSTUVHOFFVREw2RVNWWFM4MzlaRE1BRS4u";

const MC_SATISFACTION_SURVEY_LINK =
  "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=8EL7gvyBgEGl4zgLvuWNvW8FQay4Rh1FhDFQxNBKaNtUODVFSE40NjJaVVpBUUY0TDI1REkxMTBOTy4u";

function getSatisfactionSurveyLink(status) {
  if (status === "Diag finalisé") {
    return DIAG_SATISFACTION_SURVEY_LINK;
  }

  if (status === "MC finalisée") {
    return MC_SATISFACTION_SURVEY_LINK;
  }

  return null;
}


function shouldNotifySatisfactionSurvey(status) {
  return status === "Diag finalisé" || status === "MC finalisée";
}

//function shouldArchiveCompany(status) {//
//  return status === "Finalisé";//
//}//

const COMPANY_SIZES = ["<10", "11-50", ">50"];

function CompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [message, setMessage] = useState("");
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("Actifs");

  const [showCreateModal, setShowCreateModal] = useState(false);

  const [newCompany, setNewCompany] = useState({
    name: "",
    address: "",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    company_size: "",
    status: "Prospect",
});

  

  // Popups:
  // - editingDiagnosticCompany opens the Diagnostic popup.
  // - editingMissionCompany opens the Mission complémentaire popup.
  // - editingDiagnosticAxes stores selected diagnostic axes and comments.
  const [editingDiagnosticCompany, setEditingDiagnosticCompany] =
    useState(null);
  const [editingMissionCompany, setEditingMissionCompany] = useState(null);
  const [editingDiagnosticAxes, setEditingDiagnosticAxes] = useState([]);
  const [diagnosticAxesByCompanyId, setDiagnosticAxesByCompanyId] = useState({});
  const [openStateMenuCompanyId, setOpenStateMenuCompanyId] = useState(null); // this is for the dropdown color re, oraange and green 
  const [pendingArchiveCompany, setPendingArchiveCompany] = useState(null);
  
  // adding pop up for confirmation of archiving a company when status is changed to "Finalisé"
  const [archiveSuccessMessage, setArchiveSuccessMessage] = useState("");
  // for the satisfaction survey notification when status is changed to "Diag finalisé" or "MC finalisée"
  const [pendingSurveyNotification, setPendingSurveyNotification] = useState(null);

  async function loadCompanies() {
    try {
      const response = await api.get("/companies/");
      const companiesData = response.data;

      setCompanies(companiesData);

      const axesEntries = await Promise.all(
        companiesData.map(async (company) => {
          try {
            const axesResponse = await api.get(
              `/companies/${company.id}/axes-selection`
            );

            const selectedAxes = axesResponse.data.filter(
              (axis) => axis.is_selected
            );

            return [company.id, selectedAxes];
          } catch (error) {
            console.error(
              `Failed to load diagnostic axes for company ${company.id}`,
              error
            );

            return [company.id, []];
          }
        })
      );

      setDiagnosticAxesByCompanyId(Object.fromEntries(axesEntries));
    } catch (error) {
      setMessage("Failed to load companies.");
      console.error(error);
    }
  }

  useEffect(() => {
    loadCompanies();
  }, []);
  useEffect(() => {
  if (!archiveSuccessMessage) return;

  const timer = setTimeout(() => {
    setArchiveSuccessMessage("");
  }, 2500);

  return () => clearTimeout(timer);
}, [archiveSuccessMessage]);
   <strong>Attention</strong>
  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  function updateNewCompany(field, value) {
    setNewCompany((previousCompany) => ({
      ...previousCompany,
      [field]: value,
    }));
  }

  function getStateLabel(state) {
    if (state === "green") return "Bon";
    if (state === "red") return "Attention";
    return "À suivre";
  }

  async function createCompany(event) {
    event.preventDefault();

    if (!newCompany.name.trim()) {
      setMessage("Company name is required.");
      return;
    }

    try {
      await api.post("/companies/", {
        name: newCompany.name,
        address: newCompany.address || null,
        contact_name: newCompany.contact_name || null,
        contact_email: newCompany.contact_email || null,
        contact_phone: newCompany.contact_phone || null,
        company_size: newCompany.company_size || null,
        status: newCompany.status,
      });

      setMessage("Company created.");

      setNewCompany({
        name: "",
        address: "",
        contact_name: "",
        contact_email: "",
        contact_phone: "",
        company_size: "",
        status: "Prospect",
      });

      setShowCreateModal(false);
      loadCompanies();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to create company."));
      console.error(error);
    }
  }

  function openCompany(companyId) {
    window.location.href = `/companies/${companyId}`;
  }

  function openDiagnostic(companyId) {
    window.location.href = `/companies/${companyId}/diagnostic`;
  }

  function formatDate(dateValue) {
    if (!dateValue) {
      return "—";
    }

    return new Date(dateValue).toLocaleDateString("fr-FR");
  }

  function toDateInputValue(dateValue) {
    if (!dateValue) {
      return "";
    }

    return String(dateValue).slice(0, 10);
  }

  // État général is saved in the backend as:
  // green / orange / red
  // The frontend converts that into CSS classes:
  // state-green / state-orange / state-red
  function getGeneralStateClass(company) {
    const state = company.general_state || "orange";

    if (state === "green") {
      return "state-green";
    }

    if (state === "red") {
      return "state-red";
    }

    return "state-orange";
  }

  async function updateGeneralState(companyId, newStateClassName) {
    let generalState = "orange";

    if (newStateClassName === "state-green") {
      generalState = "green";
    }

    if (newStateClassName === "state-red") {
      generalState = "red";
    }

    try {
      await api.patch(`/companies/${companyId}`, {
        general_state: generalState,
      });

      setCompanies((previousCompanies) =>
        previousCompanies.map((company) =>
          company.id === companyId
            ? {
                ...company,
                general_state: generalState,
              }
            : company
        )
      );

      setMessage("État général updated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update état général."));
      console.error(error);
    }
  }

  function updateEditingDiagnostic(field, value) {
    setEditingDiagnosticCompany((previousCompany) => ({
      ...previousCompany,
      [field]: value,
    }));
  }

  function updateEditingMission(field, value) {
    setEditingMissionCompany((previousCompany) => ({
      ...previousCompany,
      [field]: value,
    }));
  }

  // Opens the Diagnostic popup.
  // It loads the axes selection from the backend first.
  async function openDiagnosticEdit(company) {
    try {
      const response = await api.get(`/companies/${company.id}/axes-selection`);

      setEditingDiagnosticCompany(company);
      setEditingDiagnosticAxes(response.data);
    } catch (error) {
      setMessage("Failed to load diagnostic axes.");
      console.error(error);
    }
  }

  // Opens the Mission complémentaire popup.
  // No axes here. Mission complémentaire only has consultant + dates.
  function openMissionEdit(company) {
    setEditingMissionCompany(company);
  }

  function getSelectedDiagnosticAxes() {
    return editingDiagnosticAxes.filter((axis) => axis.is_selected);
  }

  function getUnselectedDiagnosticAxes() {
    return editingDiagnosticAxes.filter((axis) => !axis.is_selected);
  }

  function addDiagnosticAxis(axisId) {
    if (!axisId) {
      return;
    }

    setEditingDiagnosticAxes((previousAxes) =>
      previousAxes.map((axis) =>
        Number(axis.axis_id) === Number(axisId)
          ? {
              ...axis,
              is_selected: true,
            }
          : axis
      )
    );
  }

  function removeDiagnosticAxis(axisId) {
    setEditingDiagnosticAxes((previousAxes) =>
      previousAxes.map((axis) =>
        Number(axis.axis_id) === Number(axisId)
          ? {
              ...axis,
              is_selected: false,
              diagnostic_comment: "",
            }
          : axis
      )
    );
  }

  function updateDiagnosticAxis(axisId, field, value) {
    setEditingDiagnosticAxes((previousAxes) =>
      previousAxes.map((axis) =>
        Number(axis.axis_id) === Number(axisId)
          ? {
              ...axis,
              [field]: value,
            }
          : axis
      )
    );
  }

  async function saveDiagnosticInfo() {
    if (!editingDiagnosticCompany) {
      return;
    }

    try {
      await api.patch(`/companies/${editingDiagnosticCompany.id}`, {
        diagnostic_referent:
          editingDiagnosticCompany.diagnostic_referent || null,
        diagnostic_launch_date:
          editingDiagnosticCompany.diagnostic_launch_date || null,
        diagnostic_restitution_date:
          editingDiagnosticCompany.diagnostic_restitution_date || null,
      });

      for (const axis of editingDiagnosticAxes) {
        await api.patch(
          `/companies/${editingDiagnosticCompany.id}/axes-selection/${axis.axis_id}`,
          {
            is_selected: axis.is_selected,
            diagnostic_comment: axis.diagnostic_comment || null,
          }
        );
      }

      const refreshedAxesResponse = await api.get(
        `/companies/${editingDiagnosticCompany.id}/axes-selection`
      );

      const refreshedSelectedAxes = refreshedAxesResponse.data.filter(
        (axis) => axis.is_selected
      );

      setDiagnosticAxesByCompanyId((previousData) => ({
        ...previousData,
        [editingDiagnosticCompany.id]: refreshedSelectedAxes,
      }));

      setMessage("Diagnostic information saved.");
      setEditingDiagnosticCompany(null);
      setEditingDiagnosticAxes([]);
      loadCompanies();
    } catch (error) {
      setMessage(
        getErrorMessage(error, "Failed to save diagnostic information.")
      );
      console.error(error);
    }
  }

  async function saveMissionInfo() {
    if (!editingMissionCompany) {
      return;
    }

    try {
      await api.patch(`/companies/${editingMissionCompany.id}`, {
        mission_consultant: editingMissionCompany.mission_consultant || null,
        mission_launch_date: editingMissionCompany.mission_launch_date || null,
        mission_restitution_date:
          editingMissionCompany.mission_restitution_date || null,
      });

      setMessage("Mission complémentaire information saved.");
      setEditingMissionCompany(null);
      loadCompanies();
    } catch (error) {
      setMessage(
        getErrorMessage(
          error,
          "Failed to save mission complémentaire information."
        )
      );
      console.error(error);
    }
  }

  async function confirmArchiveCompany() {
    if (!pendingArchiveCompany) return;

    try {
      await api.patch(`/companies/${pendingArchiveCompany.id}`, {
        status: "Finalisé",
        is_archived: true,
      });

      setPendingArchiveCompany(null);
      setStatusFilter("Actifs"); // Reset the filter to show active companies after archiving
      setArchiveSuccessMessage(
        "Statut mis à jour. L’entreprise a été archivée automatiquement."
      );

      await loadCompanies();
    } catch (error) {
      setMessage("Erreur lors de l’archivage automatique de l’entreprise.");
      console.error(error);
    }
  }

  function cancelArchiveCompany() {
    setPendingArchiveCompany(null);
  }

  function openSatisfactionSurvey() {
    if (!pendingSurveyNotification?.surveyLink) return;

    window.open(
      pendingSurveyNotification.surveyLink,
      "_blank",
      "noopener,noreferrer"
    );

    setPendingSurveyNotification(null);
  }

  function cancelSatisfactionSurveyPopup() {
    setPendingSurveyNotification(null);
  }


  async function updateCompanyStatus(companyId, newStatus) {
    const company = companies.find(
      (companyItem) => Number(companyItem.id) === Number(companyId)
    );

    if (newStatus === "Finalisé") {
      setPendingArchiveCompany({
        id: companyId,
        name: company?.name || "cette entreprise",
        status: newStatus,
      });

      return;
    }

    try {
      await api.patch(`/companies/${companyId}`, {
        status: newStatus,
        is_archived: false,
      });

      if (shouldNotifySatisfactionSurvey(newStatus)) {
        setPendingSurveyNotification({
          companyId: companyId,
          companyName: company?.name || "cette entreprise",
          status: newStatus,
          surveyLink: getSatisfactionSurveyLink(newStatus),
        });
      } else {
        setMessage("Statut de l’entreprise mis à jour.");
      }

      await loadCompanies();
    } catch (error) {
      setMessage("Erreur lors de la mise à jour du statut.");
      console.error(error);
    }
  }

  const filteredCompanies = useMemo(() => {
    return companies.filter((company) => {
      const text = searchText.toLowerCase();

      const matchesSearch =
        company.name?.toLowerCase().includes(text) ||
        company.address?.toLowerCase().includes(text) ||
        company.contact_name?.toLowerCase().includes(text) ||
        company.contact_email?.toLowerCase().includes(text);

      const matchesStatus =
        statusFilter === "Tous" ||
        (statusFilter === "Actifs" && !company.is_archived) ||
        (statusFilter === "Archives" && company.is_archived) ||
        company.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [companies, searchText, statusFilter]);

  return (
    <div className="app-page">
      <PortfolioHero />

      <main className="companies-page-content">
        <div className="companies-toolbar">
          <div>
            <p>{filteredCompanies.length} société(s) affichée(s)</p>
          </div>

          <button
            className="primary-button create-company-button"
            onClick={() => setShowCreateModal(true)}
          >
            + Créer une société
          </button>
        </div>

        <div className="companies-filters">
          <input
            className="company-search-input"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Rechercher une société, adresse, contact ou email..."
          />

          <select
            className="company-filter-select"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="Actifs">Actifs</option>
            <option value="Archives">Archives</option>
            <option value="Tous">Tous</option>

            {COMPANY_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {message && <p className="page-message">{message}</p>}

        <section className="company-card-list">
        {filteredCompanies.length === 0 ? (
          <div className="empty-card">
            <h3>Aucune société trouvée</h3>
            <p>Créez une société pour commencer un diagnostic.</p>
          </div>
        ) : (
          filteredCompanies.map((company, index) => {
            const generalStateClass = getGeneralStateClass(company);
            const companyDiagnosticAxes =
              diagnosticAxesByCompanyId[company.id] || [];

            return (
              <article
                key={company.id}
                className={
                  index % 2 === 0
                    ? "portfolio-company-card portfolio-company-card-light"
                    : "portfolio-company-card portfolio-company-card-muted"
                }
              >
                <div className="portfolio-company-header">
                  <div className="portfolio-company-identity">
                    <h3
                      className="portfolio-company-name"
                      onClick={() => openCompany(company.id)}
                    >
                      {company.name}
                    </h3>

                    <p className="portfolio-company-address">
                      {company.address || "Adresse non renseignée"}
                    </p>
                  </div>

                  <div className="portfolio-company-status">
                    <select
                      value={company.status || "Prospect"}
                      onChange={(event) =>
                        updateCompanyStatus(company.id, event.target.value)
                      }
                    >
                      {COMPANY_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="portfolio-company-separator"></div>

                <div className="portfolio-company-content">
                  <div className="portfolio-company-panels">
                    <section className="portfolio-info-panel">
                      <div className="portfolio-info-panel-header">
                        <button
                          type="button"
                          className="portfolio-panel-title-button"
                          onClick={() => openDiagnosticEdit(company)}
                        >
                          Diagnostic
                        </button>
                      </div>

                      <div className="portfolio-diagnostic-grid">
                        <div>
                          <p className="portfolio-panel-label">Référent</p>
                          <p className="portfolio-panel-value">
                            {company.diagnostic_referent || "—"}
                          </p>

                          <p className="portfolio-panel-label">Lancement diag</p>
                          <p className="portfolio-panel-value">
                            {formatDate(company.diagnostic_launch_date)}
                          </p>

                          <p className="portfolio-panel-label">Restitution diag</p>
                          <p className="portfolio-panel-value">
                            {formatDate(company.diagnostic_restitution_date)}
                          </p>
                        </div>

                        <div className="portfolio-diagnostic-axes">
                          {companyDiagnosticAxes.length === 0 ? (
                            <p className="portfolio-panel-value">
                              Aucun axe sélectionné
                            </p>
                          ) : (
                            companyDiagnosticAxes.map((axis) => (
                              <div
                                key={axis.axis_id}
                                className="portfolio-diagnostic-axis"
                              >
                                <p className="company-axis-name">
                                  {axis.axis_name}
                                </p>

                                <p className="company-axis-comment">
                                  Commentaire :{" "}
                                  {axis.diagnostic_comment ||
                                    "Aucun commentaire"}
                                </p>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </section>

                    <section className="portfolio-info-panel">
                      <div className="portfolio-info-panel-header">
                        <button
                          type="button"
                          className="portfolio-panel-title-button"
                          onClick={() => openMissionEdit(company)}
                        >
                          Mission complémentaire
                        </button>
                      </div>

                      <p className="portfolio-panel-label">Consultant</p>
                      <p className="portfolio-panel-value">
                        {company.mission_consultant || "—"}
                      </p>

                      <p className="portfolio-panel-label">Lancement MC</p>
                      <p className="portfolio-panel-value">
                        {formatDate(company.mission_launch_date)}
                      </p>

                      <p className="portfolio-panel-label">Restitution MC</p>
                      <p className="portfolio-panel-value">
                        {formatDate(company.mission_restitution_date)}
                      </p>
                    </section>
                  </div>

                  <div className="portfolio-company-footer">
                    <div className="portfolio-state-reactions">
                      <button
                        type="button"
                        className={`portfolio-current-state ${generalStateClass}`}
                        onClick={() =>
                          setOpenStateMenuCompanyId(
                            openStateMenuCompanyId === company.id
                              ? null
                              : company.id
                          )
                        }
                        onMouseEnter={() => setOpenStateMenuCompanyId(company.id)}
                        title={getStateLabel(company.general_state || "orange")}
                      >
                        <span className="portfolio-state-color-dot"></span>
                      </button>

                      {openStateMenuCompanyId === company.id && (
                        <div
                          className="portfolio-reaction-menu"
                          onMouseLeave={() => setOpenStateMenuCompanyId(null)}
                        >
                          <button
                            type="button"
                            className="portfolio-reaction-choice reaction-good"
                            onClick={() => {
                              updateGeneralState(company.id, "state-green");
                              setOpenStateMenuCompanyId(null);
                            }}
                          >
                            <span className="reaction-color-dot"></span>
                          </button>

                          <button
                            type="button"
                            className="portfolio-reaction-choice reaction-follow"
                            onClick={() => {
                              updateGeneralState(company.id, "state-orange");
                              setOpenStateMenuCompanyId(null);
                            }}
                          >
                            <span className="reaction-color-dot"></span>
                          </button>

                          <button
                            type="button"
                            className="portfolio-reaction-choice reaction-alert"
                            onClick={() => {
                              updateGeneralState(company.id, "state-red");
                              setOpenStateMenuCompanyId(null);
                            }}
                          >
                            <span className="reaction-color-dot"></span>
                          </button>
                        </div>
                      )}
                    </div>

                    <button
                      className="primary-button view-company-button"
                      onClick={() => openDiagnostic(company.id)}
                    >
                      Voir →
                    </button>
                  </div>
                </div>
              </article>
            );
          })
        )}
      </section>
                 
      </main>

      {showCreateModal && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Créer une société</h2>
                <p>Ajoutez les informations principales de l’entreprise.</p>
              </div>

              <button
                className="modal-close-button"
                onClick={() => setShowCreateModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={createCompany} className="company-create-form">
              <div className="form-grid-two">
                <div className="form-group">
                  <label>Nom de la société</label>
                  <input
                    value={newCompany.name}
                    onChange={(event) =>
                      updateNewCompany("name", event.target.value)
                    }
                    placeholder="Ex: Atelier Dumont & Fils"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Taille de l’entreprise</label>
                  <select
                    value={newCompany.company_size}
                    onChange={(event) =>
                      updateNewCompany("company_size", event.target.value)
                    }
                  >
                    <option value="">Choisir une taille</option>
                    {COMPANY_SIZES.map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Adresse</label>
                <input
                  value={newCompany.address}
                  onChange={(event) =>
                    updateNewCompany("address", event.target.value)
                  }
                  placeholder="Adresse complète"
                />
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Nom du contact</label>
                  <input
                    value={newCompany.contact_name}
                    onChange={(event) =>
                      updateNewCompany("contact_name", event.target.value)
                    }
                    placeholder="Nom du référent"
                  />
                </div>

                <div className="form-group">
                  <label>Email du contact</label>
                  <input
                    type="email"
                    value={newCompany.contact_email}
                    onChange={(event) =>
                      updateNewCompany("contact_email", event.target.value)
                    }
                    placeholder="contact@entreprise.fr"
                  />
                </div>
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Téléphone</label>
                  <input
                    value={newCompany.contact_phone}
                    onChange={(event) =>
                      updateNewCompany("contact_phone", event.target.value)
                    }
                    placeholder="Téléphone du contact"
                  />
                </div>

                <div className="form-group">
                  <label>Statut</label>
                  <select
                    value={newCompany.status}
                    onChange={(event) =>
                      updateNewCompany("status", event.target.value)
                    }
                  >
                    {COMPANY_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowCreateModal(false)}
                >
                  Annuler
                </button>

                <button type="submit" className="primary-button">
                  Créer la société
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingDiagnosticCompany && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Modifier le diagnostic</h2>
                <p>{editingDiagnosticCompany.name}</p>
              </div>

              <button
                className="modal-close-button"
                onClick={() => {
                  setEditingDiagnosticCompany(null);
                  setEditingDiagnosticAxes([]);
                }}
              >
                ×
              </button>
            </div>

            <div className="company-create-form">
              <div className="form-group">
                <label>Référent</label>
                <input
                  value={editingDiagnosticCompany.diagnostic_referent || ""}
                  onChange={(event) =>
                    updateEditingDiagnostic(
                      "diagnostic_referent",
                      event.target.value
                    )
                  }
                  placeholder="Nom du référent diagnostic"
                />
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Lancement diag</label>
                  <input
                    type="date"
                    value={toDateInputValue(
                      editingDiagnosticCompany.diagnostic_launch_date
                    )}
                    onChange={(event) =>
                      updateEditingDiagnostic(
                        "diagnostic_launch_date",
                        event.target.value
                      )
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Restitution diag</label>
                  <input
                    type="date"
                    value={toDateInputValue(
                      editingDiagnosticCompany.diagnostic_restitution_date
                    )}
                    onChange={(event) =>
                      updateEditingDiagnostic(
                        "diagnostic_restitution_date",
                        event.target.value
                      )
                    }
                  />
                </div>
              </div>

              <div className="axis-comments-section">
                <h3>Axes du diagnostic</h3>
                <p className="section-help">
                  Choisissez un axe dans la liste. Un champ commentaire apparaît
                  seulement pour les axes sélectionnés.
                </p>

                <div className="form-group">
                  <label>Ajouter un axe au diagnostic</label>
                  <select
                    value=""
                    onChange={(event) => addDiagnosticAxis(event.target.value)}
                  >
                    <option value="">Sélectionner un axe</option>

                    {getUnselectedDiagnosticAxes().map((axis) => (
                      <option key={axis.axis_id} value={axis.axis_id}>
                        {axis.axis_name}
                      </option>
                    ))}
                  </select>
                </div>

                {getSelectedDiagnosticAxes().length === 0 ? (
                  <p className="section-help">
                    Aucun axe sélectionné pour le diagnostic.
                  </p>
                ) : (
                  getSelectedDiagnosticAxes().map((axis) => (
                    <div key={axis.axis_id} className="axis-comment-card">
                      <div className="axis-card-header">
                        <strong>{axis.axis_name}</strong>

                        <button
                          type="button"
                          className="small-danger-button"
                          onClick={() => removeDiagnosticAxis(axis.axis_id)}
                        >
                          Retirer
                        </button>
                      </div>

                      <textarea
                        rows="3"
                        value={axis.diagnostic_comment || ""}
                        onChange={(event) =>
                          updateDiagnosticAxis(
                            axis.axis_id,
                            "diagnostic_comment",
                            event.target.value
                          )
                        }
                        placeholder="Commentaire diagnostic pour cet axe..."
                      />
                    </div>
                  ))
                )}
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setEditingDiagnosticCompany(null);
                    setEditingDiagnosticAxes([]);
                  }}
                >
                  Annuler
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={saveDiagnosticInfo}
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {pendingArchiveCompany && (
        <div className="modal-overlay">
          <div className="archive-confirmation-modal">
            <h2>Archivage automatique</h2>

            <p>
              Cette entreprise sera archivée automatiquement.
            </p>

            <p className="archive-company-name">
              {pendingArchiveCompany.name}
            </p>

            <div className="modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={cancelArchiveCompany}
              >
                Annuler
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={confirmArchiveCompany}
              >
                Continuer
              </button>
            </div>
          </div>
        </div>
      )}

      {editingMissionCompany && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Modifier la mission complémentaire</h2>
                <p>{editingMissionCompany.name}</p>
              </div>

              <button
                className="modal-close-button"
                onClick={() => setEditingMissionCompany(null)}
              >
                ×
              </button>
            </div>

            <div className="company-create-form">
              <div className="form-group">
                <label>Consultant</label>
                <input
                  value={editingMissionCompany.mission_consultant || ""}
                  onChange={(event) =>
                    updateEditingMission(
                      "mission_consultant",
                      event.target.value
                    )
                  }
                  placeholder="Nom du consultant"
                />
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Lancement MC</label>
                  <input
                    type="date"
                    value={toDateInputValue(
                      editingMissionCompany.mission_launch_date
                    )}
                    onChange={(event) =>
                      updateEditingMission(
                        "mission_launch_date",
                        event.target.value
                      )
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Restitution MC</label>
                  <input
                    type="date"
                    value={toDateInputValue(
                      editingMissionCompany.mission_restitution_date
                    )}
                    onChange={(event) =>
                      updateEditingMission(
                        "mission_restitution_date",
                        event.target.value
                      )
                    }
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setEditingMissionCompany(null)}
                >
                  Annuler
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={saveMissionInfo}
                >
                  Enregistrer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {archiveSuccessMessage && (
        <div className="modal-overlay archive-success-overlay">
          <div className="archive-success-modal small">
            <h2>Entreprise archivée</h2>

            <p>{archiveSuccessMessage}</p>
          </div>
        </div>
      )}
      {pendingSurveyNotification && (
        <div className="modal-overlay survey-notification-overlay">
          <div className="survey-notification-modal">
            <h2>Enquête de satisfaction</h2>

            <p>
              Statut mis à jour. Pensez à envoyer l’enquête de satisfaction.
            </p>

            <p className="survey-company-name">
              {pendingSurveyNotification.companyName}
            </p>

            <div className="modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={cancelSatisfactionSurveyPopup}
              >
                Annuler
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={openSatisfactionSurvey}
              >
                Ouvrir l’enquête
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CompaniesPage;
