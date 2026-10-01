import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/modals.css";
import "../styles/admin-profile-questions.css";

function AdminProfileQuestionsPage() {
  const [sections, setSections] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [message, setMessage] = useState("");

  const [showCreateSectionModal, setShowCreateSectionModal] = useState(false);
  const [editingSection, setEditingSection] = useState(null);

  const [showCreateQuestionModal, setShowCreateQuestionModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);

  const [newSection, setNewSection] = useState({
    name: "",
  });

  const [newQuestion, setNewQuestion] = useState({
    section_id: "",
    question_text: "",
  });

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadSections() {
    try {
      const response = await api.get("/admin/company-profile-sections");

      setSections(
        response.data.slice().sort((a, b) => a.order_index - b.order_index)
      );
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de charger les sections de profil."));
      console.error(error);
    }
  }

  async function loadQuestions() {
    try {
      const response = await api.get("/admin/company-profile-questions");

      setQuestions(
        response.data.slice().sort((a, b) => {
          if (a.section_order_index !== b.section_order_index) {
            return a.section_order_index - b.section_order_index;
          }

          return a.order_index - b.order_index;
        })
      );
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de charger les questions de profil."));
      console.error(error);
    }
  }

  async function loadPageData() {
    await Promise.all([loadSections(), loadQuestions()]);
  }

  useEffect(() => {
    loadPageData();
  }, []);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  function getGroupedQuestions() {
    const groups = [];

    sections
      .slice()
      .sort((a, b) => a.order_index - b.order_index)
      .forEach((section) => {
        const questionsForSection = questions
          .filter((question) => Number(question.section_id) === Number(section.id))
          .slice()
          .sort((a, b) => a.order_index - b.order_index);

        groups.push({
          section: section,
          section_id: section.id,
          section_name: section.name,
          questions: questionsForSection,
        });
      });

    return groups;
  }

  function resetNewSectionForm() {
    setNewSection({
      name: "",
    });
  }

  function resetNewQuestionForm() {
    const firstSection = sections[0];

    setNewQuestion({
      section_id: firstSection ? String(firstSection.id) : "",
      question_text: "",
    });
  }

  function updateNewSection(field, value) {
    setNewSection((previousSection) => ({
      ...previousSection,
      [field]: value,
    }));
  }

  function updateEditingSection(field, value) {
    setEditingSection((previousSection) => ({
      ...previousSection,
      [field]: value,
    }));
  }

  function updateNewQuestion(field, value) {
    setNewQuestion((previousQuestion) => ({
      ...previousQuestion,
      [field]: value,
    }));
  }

  function updateEditingQuestion(field, value) {
    setEditingQuestion((previousQuestion) => ({
      ...previousQuestion,
      [field]: value,
    }));
  }

  function openCreateSectionModal() {
    resetNewSectionForm();
    setShowCreateSectionModal(true);
  }

  function closeCreateSectionModal() {
    setShowCreateSectionModal(false);
    resetNewSectionForm();
  }

  function openEditSectionModal(section) {
    setEditingSection({
      id: section.id,
      name: section.name || "",
    });
  }

  function closeEditSectionModal() {
    setEditingSection(null);
  }

  function openCreateQuestionModal(sectionId = "") {
    resetNewQuestionForm();

    if (sectionId) {
      setNewQuestion((previousQuestion) => ({
        ...previousQuestion,
        section_id: String(sectionId),
      }));
    }

    setShowCreateQuestionModal(true);
  }

  function closeCreateQuestionModal() {
    setShowCreateQuestionModal(false);
    resetNewQuestionForm();
  }

  function openEditQuestionModal(question) {
    setEditingQuestion({
      id: question.id,
      section_id: question.section_id || "",
      question_text: question.question_text || "",
    });
  }

  function closeEditQuestionModal() {
    setEditingQuestion(null);
  }

  async function createSection(event) {
    event.preventDefault();

    if (!newSection.name.trim()) {
      setMessage("Le nom de la section est obligatoire.");
      return;
    }

    try {
      await api.post("/admin/company-profile-sections", {
        name: newSection.name.trim(),
      });

      setMessage("Section créée.");
      closeCreateSectionModal();
      await loadPageData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de créer la section."));
      console.error(error);
    }
  }

  async function saveEditingSection(event) {
    event.preventDefault();

    if (!editingSection.name.trim()) {
      setMessage("Le nom de la section est obligatoire.");
      return;
    }

    try {
      await api.patch(`/admin/company-profile-sections/${editingSection.id}`, {
        name: editingSection.name.trim(),
      });

      setMessage("Section mise à jour.");
      closeEditSectionModal();
      await loadPageData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de mettre à jour la section."));
      console.error(error);
    }
  }

  async function deleteSection(sectionId) {
    const confirmed = window.confirm(
      "Voulez-vous supprimer cette section ? Toutes ses questions et les réponses de profil associées seront également supprimées."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/company-profile-sections/${sectionId}`);

      setMessage("Section, questions et réponses supprimées.");
      await loadPageData();

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de supprimer la section."));
      console.error(error);

      return false;
    }
  }

  async function createQuestion(event) {
    event.preventDefault();

    if (!newQuestion.section_id) {
      setMessage("Veuillez choisir une section.");
      return;
    }

    if (!newQuestion.question_text.trim()) {
      setMessage("Le texte de la question est obligatoire.");
      return;
    }

    try {
      await api.post("/admin/company-profile-questions", {
        section_id: Number(newQuestion.section_id),
        question_text: newQuestion.question_text.trim(),
      });

      setMessage("Question créée.");
      closeCreateQuestionModal();
      await loadQuestions();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de créer la question."));
      console.error(error);
    }
  }

  async function saveEditingQuestion(event) {
    event.preventDefault();

    if (!editingQuestion.section_id) {
      setMessage("Veuillez choisir une section.");
      return;
    }

    if (!editingQuestion.question_text.trim()) {
      setMessage("Le texte de la question est obligatoire.");
      return;
    }

    try {
      await api.patch(`/admin/company-profile-questions/${editingQuestion.id}`, {
        section_id: Number(editingQuestion.section_id),
        question_text: editingQuestion.question_text.trim(),
      });

      setMessage("Question mise à jour.");
      closeEditQuestionModal();
      await loadQuestions();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de mettre à jour la question."));
      console.error(error);
    }
  }

  async function deleteQuestion(questionId) {
    const confirmed = window.confirm(
      "Voulez-vous supprimer cette question ? Toutes les réponses de profil associées seront également supprimées."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/company-profile-questions/${questionId}`);

      setMessage("Question et réponses supprimées.");
      await loadQuestions();

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de supprimer la question."));
      console.error(error);

      return false;
    }
  }

  function goBackToDashboard() {
    window.location.href = "/dashboard";
  }

  const groupedQuestions = getGroupedQuestions();

  return (
    <div className="app-page">
      <AppHeader
        title="Administration — Questionnaire de profil de l’entreprise"
        subtitle="Gérez les sections et les questions du profil de l’entreprise."
      />

      <main className="admin-profile-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="profile-top-bar">
          <button className="secondary-button" onClick={goBackToDashboard}>Retour au tableau de bord</button>

          <div className="profile-actions">
            <button
              className="secondary-button"
              onClick={openCreateSectionModal}
            >+ Créer une section</button>

            <button
              className="primary-button"
              onClick={() => openCreateQuestionModal()}
            >+ Créer une question</button>
          </div>
        </section>

        <section className="profile-summary-card">
          <div>
            <p className="eyebrow">Profil de l’entreprise</p>
            <h2>Configuration du questionnaire de profil</h2>
            <p>Ces questions apparaissent sur la fiche de l’entreprise et apportent un contexte utile pour l’analyse SWOT et le rapport.</p>
          </div>

          <div className="profile-summary-stats">
            <div>
              <strong>{sections.length}</strong>
              <span>sections</span>
            </div>

            <div>
              <strong>{questions.length}</strong>
              <span>questions</span>
            </div>
          </div>
        </section>

        <section className="profile-question-panel">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Questionnaire</p>
              <h2>Sections et questions</h2>
            </div>
          </div>

          {groupedQuestions.length === 0 ? (
            <div className="empty-card">
              <h3>Aucun questionnaire de profil pour le moment</h3>
              <p>Créez une section, puis ajoutez ses questions.</p>
            </div>
          ) : (
            <div className="profile-section-box-list">
              {groupedQuestions.map((group) => {
                const section = group.section;

                return (
                  <section
                    key={group.section_id}
                    className="profile-section-box"
                  >
                    <div className="profile-section-header">
                      <div>
                        <p className="eyebrow">Section</p>
                        <h3>{group.section_name}</h3>
                      </div>

                      <div className="profile-section-actions">
                        <button
                          className="small-secondary-button"
                          onClick={() => openCreateQuestionModal(section.id)}
                        >+ Ajouter une question</button>

                        <button
                          className="small-secondary-button"
                          onClick={() => openEditSectionModal(section)}
                        >Modifier la section</button>
                      </div>
                    </div>

                    <div className="profile-question-list">
                      {group.questions.length === 0 ? (
                        <div className="empty-card compact">
                          <p>Aucune question dans cette section pour le moment.</p>
                        </div>
                      ) : (
                        group.questions.map((question) => (
                          <article
                            key={question.id}
                            className="profile-question-card-admin"
                          >
                            <div className="profile-question-order">
                              {question.order_index}
                            </div>

                            <div className="profile-question-main">
                              <p className="profile-question-text">
                                {question.question_text}
                              </p>
                            </div>

                            <div className="profile-question-card-actions">
                              <button
                                className="secondary-button"
                                onClick={() => openEditQuestionModal(question)}
                              >Modifier</button>
                            </div>
                          </article>
                        ))
                      )}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {showCreateSectionModal && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Créer une section</h2>
                <p>Ajoutez une section au questionnaire de profil de l’entreprise.</p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={closeCreateSectionModal}
              >
                ×
              </button>
            </div>

            <form className="company-create-form" onSubmit={createSection}>
              <div className="form-group">
                <label>Nom de la section</label>
                <input
                  type="text"
                  value={newSection.name}
                  onChange={(event) =>
                    updateNewSection("name", event.target.value)
                  }
                  placeholder="Exemple : Informations générales"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeCreateSectionModal}
                >Annuler</button>

                <button type="submit" className="primary-button">Créer une section</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingSection && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Modifier la section</h2>
                <p>Modifiez le nom de la section.</p>
              </div>

              <div className="modal-header-actions">
                <button
                  type="button"
                  className="small-hard-delete-button"
                  onClick={async () => {
                    const success = await deleteSection(editingSection.id);

                    if (success) {
                      closeEditSectionModal();
                    }
                  }}
                >Supprimer</button>

                <button
                  type="button"
                  className="modal-close-button"
                  onClick={closeEditSectionModal}
                >
                  ×
                </button>
              </div>
            </div>

            <form className="company-create-form" onSubmit={saveEditingSection}>
              <div className="form-group">
                <label>Nom de la section</label>
                <input
                  type="text"
                  value={editingSection.name}
                  onChange={(event) =>
                    updateEditingSection("name", event.target.value)
                  }
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeEditSectionModal}
                >Annuler</button>

                <button type="submit" className="primary-button">Enregistrer les modifications</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreateQuestionModal && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Créer une question de profil</h2>
                <p>Ajoutez une question à une section du profil de l’entreprise.</p>
              </div>

              <button
                type="button"
                className="modal-close-button"
                onClick={closeCreateQuestionModal}
              >
                ×
              </button>
            </div>

            <form className="company-create-form" onSubmit={createQuestion}>
              <div className="form-group">
                <label>Section</label>
                <select
                  value={newQuestion.section_id}
                  onChange={(event) =>
                    updateNewQuestion("section_id", event.target.value)
                  }
                >
                  <option value="">Choisir une section</option>

                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Texte de la question</label>
                <textarea
                  rows="4"
                  value={newQuestion.question_text}
                  onChange={(event) =>
                    updateNewQuestion("question_text", event.target.value)
                  }
                  placeholder="Saisissez la question du profil de l’entreprise…"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeCreateQuestionModal}
                >Annuler</button>

                <button type="submit" className="primary-button">Créer une question</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingQuestion && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Modifier la question de profil</h2>
                <p>Modifiez cette question du profil de l’entreprise.</p>
              </div>

              <div className="modal-header-actions">
                <button
                  type="button"
                  className="small-hard-delete-button"
                  onClick={async () => {
                    const success = await deleteQuestion(editingQuestion.id);

                    if (success) {
                      closeEditQuestionModal();
                    }
                  }}
                >Supprimer</button>

                <button
                  type="button"
                  className="modal-close-button"
                  onClick={closeEditQuestionModal}
                >
                  ×
                </button>
              </div>
            </div>

            <form className="company-create-form" onSubmit={saveEditingQuestion}>
              <div className="form-group">
                <label>Section</label>
                <select
                  value={editingQuestion.section_id}
                  onChange={(event) =>
                    updateEditingQuestion("section_id", event.target.value)
                  }
                >
                  <option value="">Choisir une section</option>

                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Texte de la question</label>
                <textarea
                  rows="4"
                  value={editingQuestion.question_text}
                  onChange={(event) =>
                    updateEditingQuestion("question_text", event.target.value)
                  }
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeEditQuestionModal}
                >Annuler</button>

                <button type="submit" className="primary-button">Enregistrer les modifications</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminProfileQuestionsPage;