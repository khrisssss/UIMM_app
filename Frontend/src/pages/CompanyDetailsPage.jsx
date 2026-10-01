import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/company-details.css";

function CompanyDetailsPage() {
  const companyId = window.location.pathname.split("/")[2];

  const [company, setCompany] = useState(null);
  const [companyForm, setCompanyForm] = useState({
    name: "",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    address: "",
    company_size: "",
    status: "Prospect",
    prediag_origin: "",
    prediag_origin_other: "",
    has_rse: false,
    specific_regulatory_constraints: "",
    general_comment: "",
  });

  const [profileQuestions, setProfileQuestions] = useState([]);
  const [profileAnswersByQuestionId, setProfileAnswersByQuestionId] = useState(
    {}
  );

  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingCompany, setIsSavingCompany] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadCompanyDetails() {
    try {
      setIsLoading(true);

      const companyResponse = await api.get(`/companies/${companyId}`);
      const companyData = companyResponse.data;

      setCompany(companyData);

      setCompanyForm({
        name: companyData.name || "",
        contact_name: companyData.contact_name || "",
        contact_email: companyData.contact_email || "",
        contact_phone: companyData.contact_phone || "",
        address: companyData.address || "",
        company_size: companyData.company_size || "",
        status: companyData.status || "Prospect",
        prediag_origin: companyData.prediag_origin || "",
        prediag_origin_other: companyData.prediag_origin_other || "",
        has_rse: companyData.has_rse || false,
        specific_regulatory_constraints:
          companyData.specific_regulatory_constraints || "",
        general_comment: companyData.general_comment || "",
      });

      const questionsResponse = await api.get("/company-profile-questions");
      setProfileQuestions(questionsResponse.data);

      const answersResponse = await api.get(
        `/companies/${companyId}/profile-answers`
      );

      const answersMap = {};
      answersResponse.data.forEach((answer) => {
        answersMap[answer.question_id] = answer.answer_text || "";
      });

      setProfileAnswersByQuestionId(answersMap);
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de charger la fiche de l’entreprise."));
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadCompanyDetails();
  }, []);

  useEffect(() => {  // effect for the AUTO-resizing of textareas // 
  const textareas = document.querySelectorAll(".company-profile-card textarea.company-info-card textarea");

  textareas.forEach((textarea) => {
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  });
}, [profileAnswersByQuestionId]);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  useEffect(() => {
    const textareas = document.querySelectorAll(
      ".company-details-page-content textarea"
    );

    textareas.forEach((textarea) => {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    });
  }, [companyForm, profileAnswersByQuestionId]);

  function autoResizeTextarea(event) {      //adjusts the height of the textarea to fit its content// 
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
  function updateCompanyForm(field, value) {
    setCompanyForm((previousForm) => ({
      ...previousForm,
      [field]: value,
    }));
  }

  function updateProfileAnswer(questionId, value) {
    setProfileAnswersByQuestionId((previousAnswers) => ({
      ...previousAnswers,
      [questionId]: value,
    }));
  }

  function groupProfileQuestionsBySection() {
    const groups = {};

    profileQuestions.forEach((question) => {
      const sectionName = question.section_name || "Profil de l’entreprise";

      if (!groups[sectionName]) {
        groups[sectionName] = [];
      }

      groups[sectionName].push(question);
    });

    return Object.entries(groups);
  }

  async function saveCompanyInfo(event) {
    event.preventDefault();

    if (!companyForm.name.trim()) {
      setMessage("Le nom de l’entreprise est obligatoire.");
      return;
    }

    try {
      setIsSavingCompany(true);

      const payload = {
        name: companyForm.name.trim(),
        contact_name: companyForm.contact_name || null,
        contact_email: companyForm.contact_email || null,
        contact_phone: companyForm.contact_phone || null,
        address: companyForm.address || null,
        company_size: companyForm.company_size || null,
        status: companyForm.status,
        prediag_origin: companyForm.prediag_origin || null,
        prediag_origin_other: companyForm.prediag_origin_other || null,
        has_rse: companyForm.has_rse,
        specific_regulatory_constraints:
          companyForm.specific_regulatory_constraints || null,
        general_comment: companyForm.general_comment || null,
      };

      const response = await api.patch(`/companies/${companyId}`, payload);

      setCompany(response.data);
      setMessage("Informations de l’entreprise enregistrées.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de enregistrer les informations de l’entreprise."));
      console.error(error);
    } finally {
      setIsSavingCompany(false);
    }
  }

  async function hardDeleteCompany() {
    const confirmed = window.confirm(
      "Voulez-vous supprimer définitivement cette entreprise ? Ses informations, réponses de profil et de diagnostic, scores, analyses SWOT, rapports et axes sélectionnés seront également supprimés. Cette action est irréversible."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/companies/${companyId}/hard-delete`);

      setMessage("Entreprise supprimée définitivement.");

      setTimeout(() => {
        window.location.href = "/companies";
      }, 800);

      return true;
    } catch (error) {
      setMessage(
        error?.response?.data?.detail || "Impossible de supprimer définitivement l’entreprise."
      );
      console.error(error);

      return false;
    }
  }

  async function saveProfileAnswers() {
    try {
      setIsSavingProfile(true);

      for (const question of profileQuestions) {
        const answerText = profileAnswersByQuestionId[question.id] || "";

        await api.post(`/companies/${companyId}/profile-answers`, {
          question_id: question.id,
          answer_text: answerText || null,
        });
      }

      setMessage("Réponses du profil de l’entreprise enregistrées.");
      await loadCompanyDetails();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de enregistrer les réponses du profil."));
      console.error(error);
    } finally {
      setIsSavingProfile(false);
    }
  }

  function goBackToCompanies() {
    window.location.href = "/companies";
  }

  function openDiagnostic() {
    window.location.href = `/companies/${companyId}/diagnostic`;
  }

  function openAnalysis() {
    window.location.href = `/companies/${companyId}/analysis`;
  }

  function openReport() {
    window.location.href = `/companies/${companyId}/reports`;
  }

  if (isLoading) {
    return (
      <div className="app-page">
        <main className="company-details-page-content">
          <p>Chargement de la fiche de l’entreprise…</p>
        </main>
      </div>
    );
  }

  const groupedProfileQuestions = groupProfileQuestionsBySection();

  return (
    <div className="app-page">
      <AppHeader
        title={company?.name || "Fiche de l’entreprise"}
        subtitle="Identité de l’entreprise, contexte du diagnostic et questionnaire de profil."
      />

      <main className="company-details-page-content">
        {message && <div className="toast-message">{message}</div>}

        <div className="company-details-top-actions">
          <button className="secondary-button" onClick={goBackToCompanies}>Retour aux entreprises</button>

          <div className="company-details-action-group">
            <button className="primary-button" onClick={openDiagnostic}>Commencer le diagnostic</button>

            <button className="secondary-button" onClick={openAnalysis}>
              Radar / SWOT
            </button>

            <button className="secondary-button" onClick={openReport}>Rapport</button>
          </div>
        </div>

        <section className="company-details-layout">
          <form
            className="company-info-card"
            onSubmit={saveCompanyInfo}
          >
            <div className="company-info-section-header">
              <p className="eyebrow">Informations sur l’entreprise</p>
            </div>

            <div className="company-form-section">
              <div className="form-group">
                <label>Nom de l’entreprise</label>
                <input
                  type="text"
                  value={companyForm.name}
                  onChange={(event) =>
                    updateCompanyForm("name", event.target.value)
                  }
                />
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Taille de l’entreprise</label>
                  <select
                    value={companyForm.company_size}
                    onChange={(event) =>
                      updateCompanyForm("company_size", event.target.value)
                    }
                  >
                    <option value="">Choisir une taille</option>
                    <option value="<10">Moins de 10 salariés</option>
                    <option value="11-50">De 11 à 50 salariés</option>
                    <option value=">50">Plus de 50 salariés</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Statut</label>
                  <select
                    value={companyForm.status}
                    onChange={(event) =>
                      updateCompanyForm("status", event.target.value)
                    }
                  >
                    <option value="Prospect">Prospect</option>
                    <option value="Prédiag réalisé">Prédiag réalisé</option>
                    <option value="Diag en cours">Diag en cours</option>
                    <option value="Diag finalisé">Diag finalisé</option>
                    <option value="Mission Compl en cours">
                      Mission Compl en cours
                    </option>
                    <option value="MC finalisée">MC finalisée</option>
                    <option value="Finalisé">Finalisé</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Adresse</label>
                <input
                  type="text"
                  value={companyForm.address}
                  onChange={(event) =>
                    updateCompanyForm("address", event.target.value)
                  }
                />
              </div>
            </div>

            <div className="company-form-section">
              <h3>Contact</h3>

              <div className="form-group">
                <label>Nom du contact</label>
                <input
                  type="text"
                  value={companyForm.contact_name}
                  onChange={(event) =>
                    updateCompanyForm("contact_name", event.target.value)
                  }
                />
              </div>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>E-mail du contact</label>
                  <input
                    type="email"
                    value={companyForm.contact_email}
                    onChange={(event) =>
                      updateCompanyForm("contact_email", event.target.value)
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Téléphone du contact</label>
                  <input
                    type="text"
                    value={companyForm.contact_phone}
                    onChange={(event) =>
                      updateCompanyForm("contact_phone", event.target.value)
                    }
                  />
                </div>
              </div>
            </div>

            <div className="company-form-section">
              <h3>Contexte du diagnostic</h3>

              <div className="form-grid-two">
                <div className="form-group">
                  <label>Origine du prédiagnostic</label>
                  <input
                    type="text"
                    value={companyForm.prediag_origin}
                    onChange={(event) =>
                      updateCompanyForm("prediag_origin", event.target.value)
                    }
                    placeholder="Exemple : contact UIMM, événement, recommandation…"
                  />
                </div>

                <div className="form-group">
                  <label>Autre origine</label>
                  <input
                    type="text"
                    value={companyForm.prediag_origin_other}
                    onChange={(event) =>
                      updateCompanyForm(
                        "prediag_origin_other",
                        event.target.value
                      )
                    }
                  />
                </div>
              </div>

              <label className="company-rse-checkbox">
                <input
                  type="checkbox"
                  checked={companyForm.has_rse}
                  onChange={(event) =>
                    updateCompanyForm("has_rse", event.target.checked)
                  }
                />
                <span>L’entreprise a une démarche RSE</span>
              </label>

              <div className="form-group">
                <label>Contraintes réglementaires spécifiques</label>
                <textarea
                  rows="2"
                  value={companyForm.specific_regulatory_constraints}
                  onInput={autoResizeTextarea}
                  onChange={(event) =>
                    updateCompanyForm(
                      "specific_regulatory_constraints",
                      event.target.value
                    )
                  }
                  placeholder="Précisez les contraintes réglementaires, de certification, de qualité ou de sécurité…"
                />
              </div>

              <div className="form-group">
                <label>Commentaire général</label>
                <textarea
                  rows="2"
                  value={companyForm.general_comment}
                  onInput={autoResizeTextarea}
                  onChange={(event) =>
                    updateCompanyForm("general_comment", event.target.value)
                  }
                  placeholder="Contexte général du diagnostic…"
                />
              </div>
            </div>

            <div className="company-details-save-actions">
                <button
                  type="button"
                  className="company-delete-button"
                  onClick={hardDeleteCompany}
                >Supprimer l’entreprise</button>

                <button className="primary-button" onClick={saveCompanyInfo}>Enregistrer les informations de l’entreprise</button>
              </div>
          </form>

          <section className="company-profile-card">
            <div className="company-info-section-header">
              <p className="eyebrow">Profil de l’entreprise</p>
            </div>

            {profileQuestions.length === 0 ? (
              <div className="empty-card">
                <h3>Aucune question de profil</h3>
                <p>Ajoutez des questions de profil depuis l’espace d’administration.</p>
              </div>
            ) : (
              <div className="profile-question-groups">
                {groupedProfileQuestions.map(
                  ([sectionName, sectionQuestions]) => (
                    <div
                      key={sectionName}
                      className="profile-question-section"
                    >
                      <h3>{sectionName}</h3>

                      {sectionQuestions.map((question) => (
                        <div
                          key={question.id}
                          className="profile-question-card"
                        >
                          <label>{question.question_text}</label>

                          <textarea
                            rows="2"
                            value={profileAnswersByQuestionId[question.id] || ""}
                            onInput={autoResizeTextarea}
                            onChange={(event) =>
                              updateProfileAnswer(question.id,event.target.value)
                            }
                            placeholder="Saisissez la réponse de l’entreprise…"
                          />
                        </div>
                      ))}
                    </div>
                  )
                )}
              </div>
            )}

            <div className="company-details-save-actions">
              <button
                className="primary-button"
                onClick={saveProfileAnswers}
                disabled={isSavingProfile}
              >
                {isSavingProfile ? "Enregistrement en cours…" : "Enregistrer les réponses du profil"}
              </button>
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}

export default CompanyDetailsPage;