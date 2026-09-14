import { useEffect, useMemo, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/modals.css";
import "../styles/admin-axis-questions.css";

function AdminAxisQuestionsPage() {
  const queryParams = new URLSearchParams(window.location.search);
  const axisIdFromUrl = queryParams.get("axis_id");

  const [axes, setAxes] = useState([]);
  const [selectedAxisId, setSelectedAxisId] = useState(axisIdFromUrl || "");

  const [categories, setCategories] = useState([]);
  const [questions, setQuestions] = useState([]);

  const [message, setMessage] = useState("");

  const [showCreateQuestionModal, setShowCreateQuestionModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);

  const [showCreateCategoryModal, setShowCreateCategoryModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);

  const [newQuestion, setNewQuestion] = useState({
    question_text: "",
    category_id: "",
    is_active: true,
    target_less_than_10: true,
    target_11_to_50: true,
    target_more_than_50: true,
  });

  const [newCategory, setNewCategory] = useState({
    name: "",
    parent_category_id: "",
    is_active: true,
  });

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadAxes() {
    try {
      const response = await api.get("/axes/");
      const sortedAxes = response.data
        .slice()
        .sort((a, b) => a.order_index - b.order_index);

      setAxes(sortedAxes);

      if (!selectedAxisId && sortedAxes.length > 0) {
        setSelectedAxisId(String(sortedAxes[0].id));
      }
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load axes."));
      console.error(error);
    }
  }

  async function loadCategories(axisId) {
    if (!axisId) return;

    try {
      const response = await api.get(
        `/admin/axis-question-categories?axis_id=${axisId}`
      );

      setCategories(
        response.data.slice().sort((a, b) => a.order_index - b.order_index)
      );
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load categories."));
      console.error(error);
    }
  }

  async function loadQuestions(axisId) {
    if (!axisId) return;

    try {
      const response = await api.get(`/admin/axis-questions?axis_id=${axisId}`);

      setQuestions(
        response.data.slice().sort((a, b) => a.order_index - b.order_index)
      );
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load questions."));
      console.error(error);
    }
  }

  async function loadPageData(axisId) {
    await Promise.all([loadCategories(axisId), loadQuestions(axisId)]);
  }

  useEffect(() => {
    loadAxes();
  }, []);

  useEffect(() => {
    if (selectedAxisId) {
      loadPageData(selectedAxisId);
    }
  }, [selectedAxisId]);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  const selectedAxis = useMemo(() => {
    return axes.find((axis) => Number(axis.id) === Number(selectedAxisId));
  }, [axes, selectedAxisId]);



  function getParentCategories() {
    return categories.filter((category) => !category.parent_category_id);
  }

  function getGroupedQuestions() {
    const groups = [];

    const activeCategories = categories
      .filter((category) => category.is_active)
      .slice()
      .sort((a, b) => a.order_index - b.order_index);

    activeCategories.forEach((category) => {
      const activeQuestionsForCategory = questions
        .filter(
          (question) =>
            Number(question.category_id) === Number(category.id) &&
            question.is_active
        )
        .slice()
        .sort((a, b) => a.order_index - b.order_index);

      if (activeQuestionsForCategory.length > 0) {
        groups.push({
          type: "active-category",
          category_id: category.id,
          category_name: category.name,
          is_active: true,
          category: category,
          questions: activeQuestionsForCategory,
        });
      }
    });

    const activeQuestionsWithoutCategory = questions
      .filter((question) => !question.category_id && question.is_active)
      .slice()
      .sort((a, b) => a.order_index - b.order_index);

    if (activeQuestionsWithoutCategory.length > 0) {
      groups.push({
        type: "active-without-category",
        category_id: null,
        category_name: categories.length === 0 ? "Questions" : "Other questions",
        is_active: true,
        category: null,
        questions: activeQuestionsWithoutCategory,
      });
    }

    const inactiveCategories = categories
      .filter((category) => !category.is_active)
      .slice()
      .sort((a, b) => a.order_index - b.order_index);

    inactiveCategories.forEach((category) => {
      const inactiveQuestionsForCategory = questions
        .filter(
          (question) =>
            Number(question.category_id) === Number(category.id) &&
            !question.is_active
        )
        .slice()
        .sort((a, b) => a.order_index - b.order_index);

      groups.push({
        type: "inactive-category",
        category_id: category.id,
        category_name: category.name,
        is_active: false,
        category: category,
        questions: inactiveQuestionsForCategory,
      });
    });

    const inactiveQuestionsOutsideInactiveCategories = questions
      .filter((question) => {
        if (question.is_active) return false;

        const category = categories.find(
          (categoryItem) =>
            Number(categoryItem.id) === Number(question.category_id)
        );

        return !category || category.is_active;
      })
      .slice()
      .sort((a, b) => {
        const categoryA = a.category_id || 999999;
        const categoryB = b.category_id || 999999;

        if (categoryA !== categoryB) {
          return categoryA - categoryB;
        }

        return a.order_index - b.order_index;
      });

    if (inactiveQuestionsOutsideInactiveCategories.length > 0) {
      groups.push({
        type: "inactive-questions",
        category_id: "inactive-questions",
        category_name: "Deactivated questions",
        is_active: false,
        category: null,
        questions: inactiveQuestionsOutsideInactiveCategories,
      });
    }

    return groups;
  }

  function resetNewQuestionForm() {
    setNewQuestion({
      question_text: "",
      category_id: "",
      is_active: true,
      target_less_than_10: true,
      target_11_to_50: true,
      target_more_than_50: true,
    });
  }

  function resetNewCategoryForm() {
    setNewCategory({
      name: "",
      parent_category_id: "",
      is_active: true,
    });
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

  function updateNewCategory(field, value) {
    setNewCategory((previousCategory) => ({
      ...previousCategory,
      [field]: value,
    }));
  }

  function updateEditingCategory(field, value) {
    setEditingCategory((previousCategory) => ({
      ...previousCategory,
      [field]: value,
    }));
  }

  function openCreateQuestionModal() {
    resetNewQuestionForm();
    setShowCreateQuestionModal(true);
  }

  function closeCreateQuestionModal() {
    setShowCreateQuestionModal(false);
    resetNewQuestionForm();
  }

  function openEditQuestionModal(question) {
    setEditingQuestion({
      id: question.id,
      question_text: question.question_text || "",
      category_id: question.category_id || "",
      is_active: question.is_active,
      target_less_than_10: question.target_less_than_10,
      target_11_to_50: question.target_11_to_50,
      target_more_than_50: question.target_more_than_50,
    });
  }

  function closeEditQuestionModal() {
    setEditingQuestion(null);
  }

  function openCreateCategoryModal() {
    resetNewCategoryForm();
    setShowCreateCategoryModal(true);
  }

  function closeCreateCategoryModal() {
    setShowCreateCategoryModal(false);
    resetNewCategoryForm();
  }

  function openEditCategoryModal(category) {
    setEditingCategory({
      id: category.id,
      name: category.name || "",
      parent_category_id: category.parent_category_id || "",
      is_active: category.is_active,
    });
  }

  function closeEditCategoryModal() {
    setEditingCategory(null);
  }

  async function createQuestion(event) {
    event.preventDefault();

    if (!selectedAxisId) {
      setMessage("Please choose an axis first.");
      return;
    }

    if (!newQuestion.question_text.trim()) {
      setMessage("Question text is required.");
      return;
    }

    try {
      await api.post("/admin/axis-questions", {
        axis_id: Number(selectedAxisId),
        category_id: newQuestion.category_id
          ? Number(newQuestion.category_id)
          : null,
        question_text: newQuestion.question_text.trim(),
        is_active: newQuestion.is_active,
        target_less_than_10: newQuestion.target_less_than_10,
        target_11_to_50: newQuestion.target_11_to_50,
        target_more_than_50: newQuestion.target_more_than_50,
      });

      setMessage("Question created.");
      closeCreateQuestionModal();
      await loadQuestions(selectedAxisId);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to create question."));
      console.error(error);
    }
  }

  async function saveEditingQuestion(event) {
    event.preventDefault();

    if (!editingQuestion.question_text.trim()) {
      setMessage("Question text is required.");
      return;
    }

    try {
      await api.patch(`/admin/axis-questions/${editingQuestion.id}`, {
        axis_id: Number(selectedAxisId),
        category_id: editingQuestion.category_id
          ? Number(editingQuestion.category_id)
          : null,
        question_text: editingQuestion.question_text.trim(),
        is_active: editingQuestion.is_active,
        target_less_than_10: editingQuestion.target_less_than_10,
        target_11_to_50: editingQuestion.target_11_to_50,
        target_more_than_50: editingQuestion.target_more_than_50,
      });

      setMessage("Question updated.");
      closeEditQuestionModal();
      await loadQuestions(selectedAxisId);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update question."));
      console.error(error);
    }
  }

  // async function deleteQuestion(questionId) {
  //  const confirmed = window.confirm(
  //    "Are you sure you want to deactivate this question?"
  //  );

  //  if (!confirmed) return;

  //  try {
  //    await api.delete(`/admin/axis-questions/${questionId}`);
  //    setMessage("Question deactivated.");
  //    await loadQuestions(selectedAxisId);
  //  } catch (error) {
  //    setMessage(getErrorMessage(error, "Failed to deactivate question."));
  //    console.error(error);
  //  }
  //}

  //async function activateQuestion(questionId) {
  //  try {
  //    await api.patch(`/admin/axis-questions/${questionId}`, {
  //      is_active: true,
  //    });

  //    setMessage("Question activated.");
  //    await loadQuestions(selectedAxisId);
  //  } catch (error) {
  //    setMessage(getErrorMessage(error, "Failed to activate question."));
  //    console.error(error);
  //  }
  // }
  async function deactivateQuestion(questionId) {
    const confirmed = window.confirm(
      "Are you sure you want to deactivate this question?"
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/axis-questions/${questionId}`);

      setMessage("Question deactivated.");
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to deactivate question."));
      console.error(error);

      return false;
    }
  }

  async function activateQuestion(questionId) {
    try {
      await api.patch(`/admin/axis-questions/${questionId}`, {
        is_active: true,
      });

      setMessage("Question activated.");
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to activate question."));
      console.error(error);

      return false;
    }
  }

  async function hardDeleteQuestion(questionId) {
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete this question? All answers for this question will also be deleted."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/axis-questions/${questionId}/hard-delete`);

      setMessage("Question permanently deleted.");
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to permanently delete question."));
      console.error(error);

      return false;
    }
  }
  async function createCategory(event) {
    event.preventDefault();

    if (!selectedAxisId) {
      setMessage("Please choose an axis first.");
      return;
    }

    if (!newCategory.name.trim()) {
      setMessage("Category name is required.");
      return;
    }

    try {
      await api.post("/admin/axis-question-categories", {
        axis_id: Number(selectedAxisId),
        parent_category_id: newCategory.parent_category_id
          ? Number(newCategory.parent_category_id)
          : null,
        name: newCategory.name.trim(),
        is_active: newCategory.is_active,
      });

      setMessage("Category created.");
      closeCreateCategoryModal();
      await loadCategories(selectedAxisId);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to create category."));
      console.error(error);
    }
  }

  async function saveEditingCategory(event) {
    event.preventDefault();

    if (!editingCategory.name.trim()) {
      setMessage("Category name is required.");
      return;
    }

    try {
      await api.patch(
        `/admin/axis-question-categories/${editingCategory.id}`,
        {
          axis_id: Number(selectedAxisId),
          parent_category_id: editingCategory.parent_category_id
            ? Number(editingCategory.parent_category_id)
            : null,
          name: editingCategory.name.trim(),
          is_active: editingCategory.is_active,
        }
      );

      setMessage("Category updated.");
      closeEditCategoryModal();
      await loadCategories(selectedAxisId);
      await loadQuestions(selectedAxisId);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update category."));
      console.error(error);
    }
  }

//  async function deleteCategory(categoryId) {
//    const confirmed = window.confirm(
//      "Are you sure you want to deactivate this category? All questions inside it will also be deactivated."
//    );

//    if (!confirmed) return;

//    try {
//      await api.delete(`/admin/axis-question-categories/${categoryId}`);
//      setMessage("Category and questions deactivated.");
//      await loadCategories(selectedAxisId);
//      await loadQuestions(selectedAxisId);
//    } catch (error) {
//      setMessage(getErrorMessage(error, "Failed to deactivate category."));
//      console.error(error);
//    }
//  }

  //async function hardDeleteQuestion(questionId) {
  //  const confirmed = window.confirm(
  //    "Are you sure you want to permanently delete this question? All answers for this question will also be deleted."
  //  );

  //  if (!confirmed) return;

  //  try {
  //    await api.delete(`/admin/axis-questions/${questionId}/hard-delete`);

  //    setMessage("Question permanently deleted.");
  //    await loadQuestions(selectedAxisId);
  //  } catch (error) {
  //    setMessage(getErrorMessage(error, "Failed to permanently delete question."));
  //    console.error(error);
  //  }
  //}

  //async function hardDeleteCategory(categoryId) {
  //  const confirmed = window.confirm(
  //    "Are you sure you want to permanently delete this category? All questions and answers inside it will also be deleted."
  //  );

  //  if (!confirmed) return;

  //  try {
  //    await api.delete(
  //      `/admin/axis-question-categories/${categoryId}/hard-delete`
  //    );

  //    setMessage("Category, questions, and answers permanently deleted.");
  //    await loadCategories(selectedAxisId);
  //    await loadQuestions(selectedAxisId);
  //  } catch (error) {
  //    setMessage(getErrorMessage(error, "Failed to permanently delete category."));
  //    console.error(error);
  //  }
  //}

  //async function activateCategory(categoryId) {
  //  try {
  //    await api.patch(`/admin/axis-question-categories/${categoryId}`, {
  //      is_active: true,
  //    });

  //    const questionsInCategory = questions.filter(
  //      (question) => Number(question.category_id) === Number(categoryId)
  //    );

  //    await Promise.all(
  //      questionsInCategory.map((question) =>
  //        api.patch(`/admin/axis-questions/${question.id}`, {
  //          is_active: true,
  //        })
  //      )
  //    );

  //    setMessage("Category and questions activated.");
  //    await loadCategories(selectedAxisId);
  //    await loadQuestions(selectedAxisId);
  //  } catch (error) {
  //    setMessage(getErrorMessage(error, "Failed to activate category."));
  //    console.error(error);
  //  }
  //}

  async function deactivateCategory(categoryId) {
    const confirmed = window.confirm(
      "Are you sure you want to deactivate this category? All questions inside it will also be deactivated."
    );

    if (!confirmed) return false;

    try {
      await api.delete(`/admin/axis-question-categories/${categoryId}`);

      setMessage("Category and questions deactivated.");
      await loadCategories(selectedAxisId);
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to deactivate category."));
      console.error(error);

      return false;
    }
  }

  async function activateCategory(categoryId) {
    try {
      await api.patch(`/admin/axis-question-categories/${categoryId}`, {
        is_active: true,
      });

      const questionsInCategory = questions.filter(
        (question) => Number(question.category_id) === Number(categoryId)
      );

      await Promise.all(
        questionsInCategory.map((question) =>
          api.patch(`/admin/axis-questions/${question.id}`, {
            is_active: true,
          })
        )
      );

      setMessage("Category and questions activated.");
      await loadCategories(selectedAxisId);
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to activate category."));
      console.error(error);

      return false;
    }
  }

  async function hardDeleteCategory(categoryId) {
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete this category? All questions and answers inside it will also be deleted."
    );

    if (!confirmed) return false;

    try {
      await api.delete(
        `/admin/axis-question-categories/${categoryId}/hard-delete`
      );

      setMessage("Category, questions, and answers permanently deleted.");
      await loadCategories(selectedAxisId);
      await loadQuestions(selectedAxisId);

      return true;
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to permanently delete category."));
      console.error(error);

      return false;
    }
  }
  async function moveCategory(categoryId, direction) {
    const sortedCategories = categories
      .slice()
      .sort((a, b) => a.order_index - b.order_index);

    const currentIndex = sortedCategories.findIndex(
      (category) => Number(category.id) === Number(categoryId)
    );

    if (currentIndex === -1) return;

    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;

    if (newIndex < 0 || newIndex >= sortedCategories.length) return;

    const reorderedCategories = [...sortedCategories];
    const [movedCategory] = reorderedCategories.splice(currentIndex, 1);
    reorderedCategories.splice(newIndex, 0, movedCategory);

    const orderedCategoryIds = reorderedCategories.map((category) => category.id);

    try {
      await api.patch(
        `/admin/axis-question-categories/${selectedAxisId}/reorder`,
        {
          ordered_category_ids: orderedCategoryIds,
        }
      );

      setMessage("Categories reordered.");
      await loadCategories(selectedAxisId);
      await loadQuestions(selectedAxisId);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to reorder categories."));
      console.error(error);
    }
  }

  async function moveQuestion(questionId, categoryId, direction) {
    const sameGroupQuestions = questions
      .filter((question) => {
        const currentCategory = question.category_id || null;
        const targetCategory = categoryId || null;

        return (
          currentCategory === targetCategory &&
          question.is_active
        );
      })
      .sort((a, b) => a.order_index - b.order_index);

    const currentIndex = sameGroupQuestions.findIndex(
      (question) => Number(question.id) === Number(questionId)
    );

    if (currentIndex === -1) return;

    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;

    if (newIndex < 0 || newIndex >= sameGroupQuestions.length) return;

    const reorderedQuestions = [...sameGroupQuestions];
    const [movedQuestion] = reorderedQuestions.splice(currentIndex, 1);
    reorderedQuestions.splice(newIndex, 0, movedQuestion);

    const orderedQuestionIds = reorderedQuestions.map((question) => question.id);

    try {
      await api.patch(`/admin/axis-questions/${selectedAxisId}/reorder`, {
        category_id: categoryId || null,
        ordered_question_ids: orderedQuestionIds,
      });

      setMessage("Questions reordered.");
      await loadQuestions(selectedAxisId);
    } catch (error) {
      console.error("Question reorder error:", error.response?.data || error);
      setMessage(getErrorMessage(error, "Failed to reorder questions."));
    }
  }

  function goBackToDashboard() {
    window.location.href = "/dashboard";
  }

  const groupedQuestions = getGroupedQuestions();

  return (
    <div className="app-page">
      <AppHeader
        title="Admin — Axis questions"
        subtitle="Manage questions, categories, order, and company size targeting."
      />

      <main className="admin-axis-questions-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="axis-question-top-bar">
          <button className="secondary-button" onClick={goBackToDashboard}>
            Back to dashboard
          </button>

          <div className="axis-question-actions">
            <button
              className="secondary-button"
              onClick={openCreateCategoryModal}
            >
              + Create category
            </button>

            <button className="primary-button" onClick={openCreateQuestionModal}>
              + Create question
            </button>
          </div>
        </section>

        <section className="axis-question-control-card">
          <div>
            <h2>{selectedAxis?.name || "Choose an axis"}</h2>
            <p>Select an axis to manage its categories and questions.</p>
          </div>

          <div className="form-group axis-select-box">
            <label>Axis</label>
            <select
              value={selectedAxisId}
              onChange={(event) => setSelectedAxisId(event.target.value)}
            >
              <option value="">Choose an axis</option>

              {axes.map((axis) => (
                <option key={axis.id} value={axis.id}>
                  {axis.order_index}. {axis.name}
                </option>
              ))}
            </select>
          </div>
        </section>

        <section className="questions-panel full-width">          
          {groupedQuestions.length === 0 ? (
            <div className="empty-card">
              <h3>No questions</h3>
              <p>Create the first question for this axis.</p>
            </div>
          ) : (
            <div className="question-category-box-list">
              {groupedQuestions.map((group) => {
                const category = group.category;

                return (
                  <section
                    key={`${group.type}-${group.category_id || "without-category"}`}
                    className={
                      group.is_active
                        ? "question-category-box"
                        : "question-category-box inactive-category-box"
                    }
                  >
                    <div className="question-category-header">
                      <div>
                          <h3>{group.category_name}</h3>

                          {category?.parent_category_name && (
                            <p>Parent: {category.parent_category_name}</p>
                        )}

                        {!category && (
                          <p>
                            {group.type === "inactive-questions"
                              ? "Questions deactivated individually."
                              : categories.length === 0
                              ? "Questions for this axis."
                              : "Other questions for this axis."}
                          </p>
                        )}
                      </div>

                      {category && (
                        <div className="question-category-actions">
                          {group.is_active ? (
                            <>
                              <button
                                className="small-secondary-button"
                                onClick={() => moveCategory(category.id, "up")}
                              >
                                ↑
                              </button>

                              <button
                                className="small-secondary-button"
                                onClick={() => moveCategory(category.id, "down")}
                              >
                                ↓
                              </button>

                              <button
                                className="small-secondary-button"
                                onClick={() => openEditCategoryModal(category)}
                              >
                                Edit category
                              </button>
                                    
                            </>
                          ) : (
                            <>
                              <button
                                className="small-secondary-button"
                                onClick={() => openEditCategoryModal(category)}
                              >
                                Edit category
                              </button>
                              
                            </>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="question-list-inside-category">
                      {group.questions.length === 0 ? (
                        <div className="empty-card compact">
                          <p>No questions in this category.</p>
                        </div>
                      ) : (
                        group.questions
                          .slice()
                          .sort((a, b) => a.order_index - b.order_index)
                          .map((question, index) => (
                            <article
                              key={question.id}
                              className={
                                question.is_active
                                  ? "admin-question-card"
                                  : "admin-question-card inactive"
                              }
                            >
                              <div className="question-order">
                                {question.order_index}
                              </div>

                              <div className="question-main">
                                <p className="question-text">
                                  {question.question_text}
                                </p>


                                <div className="question-size-tags">
                                  {question.target_less_than_10 && (
                                    <span>{"<10"}</span>
                                  )}

                                  {question.target_11_to_50 && (
                                    <span>11-50</span>
                                  )}

                                  {question.target_more_than_50 && (
                                    <span>{">50"}</span>
                                  )}
                                </div>
                              </div>

                              <div className="admin-question-actions">
                                <button
                                  className="small-secondary-button"
                                  disabled={
                                    index === 0 ||
                                    !group.is_active ||
                                    !question.is_active
                                  }
                                  onClick={() =>
                                    moveQuestion(
                                      question.id,
                                      question.category_id,
                                      "up"
                                    )
                                  }
                                >
                                  ↑
                                </button>

                                <button
                                  className="small-secondary-button"
                                  disabled={
                                    index === group.questions.length - 1 ||
                                    !group.is_active ||
                                    !question.is_active
                                  }
                                  onClick={() =>
                                    moveQuestion(
                                      question.id,
                                      question.category_id,
                                      "down"
                                    )
                                  }
                                >
                                  ↓
                                </button>

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

      {showCreateQuestionModal && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Create question</h2>
                <p>Add a diagnostic question to the selected axis.</p>
              </div>

              <button
                className="modal-close-button"
                onClick={closeCreateQuestionModal}
              >
                ×
              </button>
            </div>

            <form className="company-create-form" onSubmit={createQuestion}>
              <div className="form-group">
                <label>Question text</label>
                <textarea
                  rows="4"
                  value={newQuestion.question_text}
                  onChange={(event) =>
                    updateNewQuestion("question_text", event.target.value)
                  }
                  placeholder="Write the diagnostic question..."
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <select
                  value={newQuestion.category_id}
                  onChange={(event) =>
                    updateNewQuestion("category_id", event.target.value)
                  }
                >
                  <option value="">Without category</option>

                  {categories
                    .filter((category) => category.is_active)
                    .map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                </select>
              </div>

              <div className="question-target-box">
                <p>Show this question for company size:</p>

                <label>
                  <input
                    type="checkbox"
                    checked={newQuestion.target_less_than_10}
                    onChange={(event) =>
                      updateNewQuestion(
                        "target_less_than_10",
                        event.target.checked
                      )
                    }
                  />
                  {"<10"}
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={newQuestion.target_11_to_50}
                    onChange={(event) =>
                      updateNewQuestion(
                        "target_11_to_50",
                        event.target.checked
                      )
                    }
                  />
                  11-50
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={newQuestion.target_more_than_50}
                    onChange={(event) =>
                      updateNewQuestion(
                        "target_more_than_50",
                        event.target.checked
                      )
                    }
                  />
                  {">50"}
                </label>
              </div>

              <label className="admin-axis-checkbox">
                <input
                  type="checkbox"
                  checked={newQuestion.is_active}
                  onChange={(event) =>
                    updateNewQuestion("is_active", event.target.checked)
                  }
                />
                <span>Active question</span>
              </label>

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

      {editingQuestion && (    // pop up table to edit //
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Edit question</h2>
                <p>Update this diagnostic question.</p>
              </div>

              <div className="modal-header-actions">
                {editingQuestion.is_active ? (
                  <button
                    type="button"
                    className="small-danger-button"
                    onClick={async () => {
                      const success = await deactivateQuestion(editingQuestion.id);

                      if (success) {
                        closeEditQuestionModal();
                      }
                    }}
                  >
                    Deactivate
                  </button>
                ) : (
                  <button
                    type="button"
                    className="small-activate-button"
                    onClick={async () => {
                      const success = await activateQuestion(editingQuestion.id);

                      if (success) {
                        closeEditQuestionModal();
                      }
                    }}
                  >
                    Activate
                  </button>
                )}

                <button
                  type="button"
                  className="small-hard-delete-button"
                  onClick={async () => {
                    const success = await hardDeleteQuestion(editingQuestion.id);

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

            <form
              className="company-create-form"
              onSubmit={saveEditingQuestion}
            >
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

              <div className="form-group">
                <label>Category</label>
                <select
                  value={editingQuestion.category_id}
                  onChange={(event) =>
                    updateEditingQuestion("category_id", event.target.value)
                  }
                >
                  <option value="">Without category</option>

                  {categories
                    .filter((category) => category.is_active)
                    .map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                </select>
              </div>

              <div className="question-target-box">
                <p>Show this question for company size:</p>

                <label>
                  <input
                    type="checkbox"
                    checked={editingQuestion.target_less_than_10}
                    onChange={(event) =>
                      updateEditingQuestion(
                        "target_less_than_10",
                        event.target.checked
                      )
                    }
                  />
                  {"<10"}
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={editingQuestion.target_11_to_50}
                    onChange={(event) =>
                      updateEditingQuestion(
                        "target_11_to_50",
                        event.target.checked
                      )
                    }
                  />
                  11-50
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={editingQuestion.target_more_than_50}
                    onChange={(event) =>
                      updateEditingQuestion(
                        "target_more_than_50",
                        event.target.checked
                      )
                    }
                  />
                  {">50"}
                </label>
              </div>

              <label className="admin-axis-checkbox">
                <input
                  type="checkbox"
                  checked={editingQuestion.is_active}
                  onChange={(event) =>
                    updateEditingQuestion("is_active", event.target.checked)
                  }
                />
                <span>Active question</span>
              </label>

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

      {showCreateCategoryModal && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Create category</h2>
                <p>Add a category for the selected axis.</p>
              </div>

              <button
                className="modal-close-button"
                onClick={closeCreateCategoryModal}
              >
                ×
              </button>
            </div>

            <form className="company-create-form" onSubmit={createCategory}>
              <div className="form-group">
                <label>Category name</label>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={(event) =>
                    updateNewCategory("name", event.target.value)
                  }
                  placeholder="Example: Gouvernance"
                />
              </div>

              <div className="form-group">
                <label>Parent category</label>
                <select
                  value={newCategory.parent_category_id}
                  onChange={(event) =>
                    updateNewCategory(
                      "parent_category_id",
                      event.target.value
                    )
                  }
                >
                  <option value="">No parent</option>

                  {getParentCategories()
                    .filter((category) => category.is_active)
                    .map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                </select>
              </div>

              <label className="admin-axis-checkbox">
                <input
                  type="checkbox"
                  checked={newCategory.is_active}
                  onChange={(event) =>
                    updateNewCategory("is_active", event.target.checked)
                  }
                />
                <span>Active category</span>
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeCreateCategoryModal}
                >
                  Cancel
                </button>

                <button type="submit" className="primary-button">
                  Create category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingCategory && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Edit category</h2>
                <p>Update this category.</p>
              </div>

              <div className="modal-header-actions">
                {editingCategory.is_active ? (
                  <button
                    type="button"
                    className="small-danger-button"
                    onClick={async () => {
                      const success = await deactivateCategory(editingCategory.id);

                      if (success) {
                        closeEditCategoryModal();
                      }
                    }}
                  >
                    Deactivate
                  </button>
                ) : (
                  <button
                    type="button"
                    className="small-activate-button"
                    onClick={async () => {
                      const success = await activateCategory(editingCategory.id);

                      if (success) {
                        closeEditCategoryModal();
                      }
                    }}
                  >
                    Activate
                  </button>
                )}

                <button
                  type="button"
                  className="small-hard-delete-button"
                  onClick={async () => {
                    const success = await hardDeleteCategory(editingCategory.id);

                    if (success) {
                      closeEditCategoryModal();
                    }
                  }}
                >
                  Delete
                </button>

                <button
                  type="button"
                  className="modal-close-button"
                  onClick={closeEditCategoryModal}
                >
                  ×
                </button>
              </div>
            </div>

            <form className="company-create-form" onSubmit={saveEditingCategory}>
              <div className="form-group">
                <label>Category name</label>
                <input
                  type="text"
                  value={editingCategory.name}
                  onChange={(event) =>
                    updateEditingCategory("name", event.target.value)
                  }
                />
              </div>

              <div className="form-group">
                <label>Parent category</label>
                <select
                  value={editingCategory.parent_category_id}
                  onChange={(event) =>
                    updateEditingCategory(
                      "parent_category_id",
                      event.target.value
                    )
                  }
                >
                  <option value="">No parent</option>

                  {getParentCategories()
                    .filter(
                      (category) =>
                        Number(category.id) !== Number(editingCategory.id) &&
                        category.is_active
                    )
                    .map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                </select>
              </div>

              <label className="admin-axis-checkbox">
                <input
                  type="checkbox"
                  checked={editingCategory.is_active}
                  onChange={(event) =>
                    updateEditingCategory("is_active", event.target.checked)
                  }
                />
                <span>Active category</span>
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeEditCategoryModal}
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

export default AdminAxisQuestionsPage;