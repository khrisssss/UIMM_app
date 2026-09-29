import { useEffect, useMemo, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/questionnaire.css";

function AxisQuestionnairePage() {
  const pathParts = window.location.pathname.split("/");
  const companyId = pathParts[2];
  const axisId = pathParts[4];

  const [company, setCompany] = useState(null);
  const [axis, setAxis] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answersByQuestionId, setAnswersByQuestionId] = useState({});
  const [scoringLevels, setScoringLevels] = useState([]);

  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
 
  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }
  useEffect(() => {
    loadQuestionnaireData();
  }, []);

  useEffect(() => {
    if (!isLoading && axis?.name?.trim().toLowerCase() === "finance" && questions.length === 0) {
      window.location.replace(`/companies/${companyId}/finance`);
    }
  }, [isLoading, axis, questions.length, companyId]);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  useEffect(() => {    // This resizes once immediately, then again after React finishes displaying the saved answers.//
    function resizeAllTextareas() {
      const textareas = document.querySelectorAll(
        ".questionnaire-page-content textarea"
      );

      textareas.forEach((textarea) => {
        textarea.style.height = "auto";
        textarea.style.height = `${textarea.scrollHeight}px`;
      });
    }

    resizeAllTextareas();

    const timer = setTimeout(() => {
      resizeAllTextareas();
    }, 100);

    return () => clearTimeout(timer);
  }, [answersByQuestionId, questions, isLoading]);

  function autoResizeTextarea(event) {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  async function loadQuestionnaireData() {
    try {
      setIsLoading(true);

      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const axesResponse = await api.get("/axes/");
      const currentAxis = axesResponse.data.find(
        (axisItem) => Number(axisItem.id) === Number(axisId)
      );
      setAxis(currentAxis || null);

      const questionsResponse = await api.get(
        `/companies/${companyId}/diagnostic/axes/${axisId}/questions`
      );
      setQuestions(questionsResponse.data);

      const answersResponse = await api.get(`/companies/${companyId}/answers`);

      const answersMap = {};
      answersResponse.data.forEach((answer) => {
        answersMap[answer.question_id] = {
          score_code: answer.score_code || "",
          comment: answer.comment || "",
          answer_text: answer.answer_text || "",
        };
      });

      setAnswersByQuestionId(answersMap);

      try {
        const scoringResponse = await api.get(
          `/axes/${axisId}/scoring-scales`
        );

        const scales = scoringResponse.data;

        if (Array.isArray(scales) && scales.length > 0) {
          setScoringLevels(scales[0].levels || []);
        } else if (scales?.levels) {
          setScoringLevels(scales.levels || []);
        } else {
          setScoringLevels([]);
        }
      } catch (error) {
        console.warn("No scoring scale found for this axis.", error);
        setScoringLevels([]);
      }
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load questionnaire."));
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

 

  

  function updateAnswer(questionId, field, value) {
    setAnswersByQuestionId((previousAnswers) => ({
      ...previousAnswers,
      [questionId]: {
        score_code: previousAnswers[questionId]?.score_code || "",
        comment: previousAnswers[questionId]?.comment || "",
        answer_text: previousAnswers[questionId]?.answer_text || "",
        [field]: value,
      },
    }));
  }

  function getAnswerForQuestion(questionId) {
    return (
      answersByQuestionId[questionId] || {
        score_code: "",
        comment: "",
        answer_text: "",
      }
    );
  }

  function getGroupedQuestions() {
    const groups = [];

    questions.forEach((question) => {
      const categoryName = question.category_name || "Questions";
      const categoryId = question.category_id || "without-category";

      let group = groups.find(
        (groupItem) => String(groupItem.categoryId) === String(categoryId)
      );

      if (!group) {
        group = {
          categoryId: categoryId,
          categoryName: categoryName,
          categoryOrderIndex: question.category_order_index || 999999,
          questions: [],
        };

        groups.push(group);
      }

      group.questions.push(question);
    });

    return groups
      .sort((a, b) => a.categoryOrderIndex - b.categoryOrderIndex)
      .map((group) => [
        group.categoryName,
        group.questions.sort((a, b) => a.order_index - b.order_index),
      ]);
  }

  function getAnsweredQuestionsCount() {
    return questions.filter((question) => {
      const answer = getAnswerForQuestion(question.id);
      return answer.score_code && answer.score_code !== "";
    }).length;
  }

  function getProgressPercentage() {
    if (questions.length === 0) {
      return 0;
    }

    return Math.round((getAnsweredQuestionsCount() / questions.length) * 100);
  }

  function getProgressClass(percentage) {
    if (percentage >= 100) {
      return "progress-green";
    }

    if (percentage >= 50) {
      return "progress-orange";
    }

    return "progress-red";
  }

  const progressPercentage = getProgressPercentage();
  const progressClass = getProgressClass(progressPercentage);

  const groupedQuestions = useMemo(() => getGroupedQuestions(), [
    questions,
    answersByQuestionId,
  ]);

  async function saveAllAnswers() {
    try {
      setIsSaving(true);

      for (const question of questions) {
        const answer = getAnswerForQuestion(question.id);

        const hasScore = answer.score_code && answer.score_code !== "";
        const hasComment = answer.comment && answer.comment.trim() !== "";

        // Do not save empty answers
        if (!hasScore && !hasComment) {
          continue;
        }

        // If there is a comment but no score, stop and explain
        if (!hasScore && hasComment) {
          setMessage(
            "Please choose a score for every question that has a comment."
          );
          setIsSaving(false);
          return;
        }

      await api.post(`/companies/${companyId}/answers`, {
        question_id: question.id,
        score_code: answer.score_code,
        answer_text: null,
        comment: answer.comment || null,
      });
    }

      await api.post(`/companies/${companyId}/calculate-scores`);

      setMessage("Answers saved and scores updated.");
      await loadQuestionnaireData();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to save answers."));
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  }

  function goBackToDiagnostic() {
    window.location.href = `/companies/${companyId}/diagnostic`;
  }

  function openAnalysis() {
    window.location.href = `/companies/${companyId}/analysis`;
  }

  if (!isLoading && axis?.name?.trim().toLowerCase() === "finance" && questions.length === 0) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="app-page">
        <main className="questionnaire-page-content">
          <p>Loading questionnaire...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="app-page">
      <AppHeader
        title={company ? company.name : "Questionnaire"}
        subtitle={axis ? `Questionnaire — ${axis.name}` : "Questionnaire"}
      />

      <main className="questionnaire-page-content">
        <div className="questionnaire-top-actions">
          <button className="secondary-button" onClick={goBackToDiagnostic}>
            Back to diagnostic overview
          </button>

          {axis?.name?.trim().toLowerCase() === "finance" && (
            <button className="secondary-button" onClick={() => window.location.href = `/companies/${companyId}/finance`}>
              Financial figures and projections
            </button>
          )}
          <button className="primary-button" onClick={openAnalysis}>
            View Radar / SWOT
          </button>
        </div>

        {message && (
          <div className="toast-message">
            {message}
          </div>
        )}
        <section className="questionnaire-summary-card">
          <div>
            <h2>{axis?.name || "Axis"}</h2> 

            <p>
              <strong>{getAnsweredQuestionsCount()}</strong> /{" "}
              <strong>{questions.length}</strong> questions answered
            </p>

            <p>{progressPercentage}% completed</p>
          </div>

          <div className="questionnaire-progress-area">
            <div className="progress-bar-background">
              <div
                className={`progress-bar-fill ${progressClass}`}
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
        </section>

        {scoringLevels.length === 0 ? (
          <div className="empty-card">
            <h3>No scoring scale found</h3>
            <p>
              This axis does not have a scoring scale. You can still display
              questions, but score dropdowns cannot be shown.
            </p>
          </div>
        ) : null}

        <section className="questionnaire-list">
          {questions.length === 0 ? (
            <div className="empty-card">
              <h3>No questions found</h3>
              <p>No questions are available for this company and axis.</p>
            </div>
          ) : (
            groupedQuestions.map(([categoryName, categoryQuestions]) => (
              <div key={categoryName} className="question-category-block">
                <h3>{categoryName}</h3>

                {categoryQuestions.map((question, index) => {
                  const answer = getAnswerForQuestion(question.id);

                  return (
                    <article key={question.id} className="question-card">
                      <div className="question-header">
                        <span className="question-number">
                          Question {index + 1}
                        </span>

                        <span className="question-max-score">
                          Max score: {question.max_score}
                        </span>
                      </div>

                      <p className="question-text">{question.question_text}</p>

                      <div className="question-answer-grid">
                        <div className="form-group">
                          <label>Score</label>

                          <select
                            value={answer.score_code}
                            onChange={(event) =>
                              updateAnswer(
                                question.id,
                                "score_code",
                                event.target.value
                              )
                            }
                          >
                            <option value="">Choose a score</option>

                            {scoringLevels.map((level) => (
                              <option key={level.id} value={level.code}>
                                {level.code}
                                {level.label ? ` — ${level.label}` : ""}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label>Consultant comment</label>

                          <textarea
                            rows="2"
                            value={getAnswerForQuestion(question.id).comment || ""}
                            onInput={autoResizeTextarea}
                            onChange={(event) =>
                              updateAnswer(question.id, "comment", event.target.value)
                            }
                            placeholder="Add comment..."
                          />
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            ))
          )}
        </section>

        <div className="questionnaire-save-bar">
          <button
            className="primary-button"
            onClick={saveAllAnswers}
            disabled={isSaving}
          >
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </main>
    </div>
  );
}
export default AxisQuestionnairePage;