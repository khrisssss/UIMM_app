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
      setMessage(getErrorMessage(error, "Failed to load profile sections."));
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
      setMessage(getErrorMessage(error, "Failed to load profile questions."));
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
      setMessage("Section name is required.");
      return;
    }

    try {
      await api.post("/admin/company-profile-sections", {
        name: newSection.name.trim(),
      });

      setMessage("Section created.");
      closeCreateSectionModal();
      await loadPageData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to create section."));
      console.error(error);
    }
  }

  async function saveEditingSection(event) {
    event.preventDefault();

    if (!editingSection.name.trim()) {
      setMessage("Section name is required.");
      return;
    }

    try {
      await api.patch(`/admin/company-profile-sections/${editingSection.id}`, {
        name: editingSection.name.trim(),
      });

      setMessage("Section updated.");
      closeEditSectionModal();
      await loadPageData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update section."));
      console.error(error);
    }
  }

  async function deleteSection(sectionId) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this section? All questions inside it and all related company profile answers will also be deleted."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/company-profile-sections/${sectionId}`);

      setMessage("Section, questions, and answers deleted.");
      await loadPageData();

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to delete section."));
      console.error(error);

      return false;
    }
  }

  async function createQuestion(event) {
    event.preventDefault();

    if (!newQuestion.section_id) {
      setMessage("Please choose a section.");
      return;
    }

    if (!newQuestion.question_text.trim()) {
      setMessage("Question text is required.");
      return;
    }

    try {
      await api.post("/admin/company-profile-questions", {
        section_id: Number(newQuestion.section_id),
        question_text: newQuestion.question_text.trim(),
      });

      setMessage("Question created.");
      closeCreateQuestionModal();
      await loadQuestions();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to create question."));
      console.error(error);
    }
  }

  async function saveEditingQuestion(event) {
    event.preventDefault();

    if (!editingQuestion.section_id) {
      setMessage("Please choose a section.");
      return;
    }

    if (!editingQuestion.question_text.trim()) {
      setMessage("Question text is required.");
      return;
    }

    try {
      await api.patch(`/admin/company-profile-questions/${editingQuestion.id}`, {
        section_id: Number(editingQuestion.section_id),
        question_text: editingQuestion.question_text.trim(),
      });

      setMessage("Question updated.");
      closeEditQuestionModal();
      await loadQuestions();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update question."));
      console.error(error);
    }
  }

  async function deleteQuestion(questionId) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this question? All related company profile answers will also be deleted."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/company-profile-questions/${questionId}`);

      setMessage("Question and answers deleted.");
      await loadQuestions();

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to delete question."));
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
        title="Admin — Company profile questionnaire"
        subtitle="Manage company profile sections and questions."
      />

      <main className="admin-profile-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="profile-top-bar">
          <button className="secondary-button" onClick={goBackToDashboard}>
            Back to dashboard
          </button>

          <div className="profile-actions">
            <button
              className="secondary-button"
              onClick={openCreateSectionModal}
            >
              + Create section
            </button>

            <button
              className="primary-button"
              onClick={() => openCreateQuestionModal()}
            >
              + Create question
            </button>
          </div>
        </section>

        <section className="profile-summary-card">
          <div>
            <p className="eyebrow">Company profile</p>
            <h2>Profile questionnaire setup</h2>
            <p>
              These questions appear on the company information page and give
              useful context for the SWOT and future report.
            </p>
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
              <h2>Sections and questions</h2>
            </div>
          </div>

          {groupedQuestions.length === 0 ? (
            <div className="empty-card">
              <h3>No profile questionnaire yet</h3>
              <p>Create a section first, then add questions inside it.</p>
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
                        >
                          + Add question
                        </button>

                        <button
                          className="small-secondary-button"
                          onClick={() => openEditSectionModal(section)}
                        >
                          Edit section
                        </button>
                      </div>
                    </div>

                    <div className="profile-question-list">
                      {group.questions.length === 0 ? (
                        <div className="empty-card compact">
                          <p>No questions in this section yet.</p>
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
                              >
                                Edit
                              </button>
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
                <h2>Create section</h2>
                <p>Add a new section to the company profile questionnaire.</p>
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
                <label>Section name</label>
                <input
                  type="text"
                  value={newSection.name}
                  onChange={(event) =>
                    updateNewSection("name", event.target.value)
                  }
                  placeholder="Example: Informations générales"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeCreateSectionModal}
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  Create section
                </button>
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
                <h2>Edit section</h2>
                <p>Update the section name.</p>
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
                >
                  Delete
                </button>

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
                <label>Section name</label>
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
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  Save changes
                </button>
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
                <h2>Create profile question</h2>
                <p>Add a question inside a company profile section.</p>
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
                  <option value="">Choose a section</option>

                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Question text</label>
                <textarea
                  rows="4"
                  value={newQuestion.question_text}
                  onChange={(event) =>
                    updateNewQuestion("question_text", event.target.value)
                  }
                  placeholder="Write the company profile question..."
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeCreateQuestionModal}
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  Create question
                </button>
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
                <h2>Edit profile question</h2>
                <p>Update this company profile question.</p>
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
                >
                  Delete
                </button>

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
                  <option value="">Choose a section</option>

                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Question text</label>
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
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  Save changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminProfileQuestionsPage;