import { useEffect, useState } from "react";

import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";
import "../styles/modals.css";
import "../styles/admin-axes.css";

function AdminAxesPage() {
  const [axes, setAxes] = useState([]);
  const [message, setMessage] = useState("");

  const [editingAxis, setEditingAxis] = useState(null);
  //const [axisScoringScale, setAxisScoringScale] = useState(null);
  //const [isLoadingScoring, setIsLoadingScoring] = useState(false);

  function getErrorMessage(error, fallbackMessage) {
    return error?.response?.data?.detail || fallbackMessage;
  }

  async function loadAxes() {
    try {
      const response = await api.get("/axes/");
      setAxes(response.data);
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to load axes."));
      console.error(error);
    }
  }


  useEffect(() => {
    loadAxes();
  }, []);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setMessage("");
    }, 4000);

    return () => clearTimeout(timer);
  }, [message]);

  function updateEditingAxis(field, value) {
    setEditingAxis((previousAxis) => ({
      ...previousAxis,
      [field]: value,
    }));
  }

  function openEditModal(axis) {
    setEditingAxis({
      id: axis.id,
      name: axis.name || "",
      description: axis.description || "",
      order_index: axis.order_index || 1,
      is_active: axis.is_active,
    });
  }

  function closeEditModal() {
    setEditingAxis(null);
  }

  async function saveEditingAxis(event) {
    event.preventDefault();

    if (!editingAxis.name.trim()) {
      setMessage("Axis name is required.");
      return;
    }

    try {
      await api.patch(`/axes/${editingAxis.id}`, {
        name: editingAxis.name.trim(),
        description: editingAxis.description || null,
        order_index: Number(editingAxis.order_index),
        is_active: editingAxis.is_active,
      });

      setMessage("Axis updated.");
      closeEditModal();
      await loadAxes();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to update axis."));
      console.error(error);
    }
  }
 

  function openAxisQuestions(axisId) {
    window.location.href = `/admin/axis-questions?axis_id=${axisId}`;
  }

  function goBackDashboard() {
    window.location.href = "/dashboard";
  }

  const activeAxes = axes.filter((axis) => axis.is_active);
  const inactiveAxes = axes.filter((axis) => !axis.is_active);

  return (
    <div className="app-page">
      <AppHeader
        title="Admin — Axes"
        subtitle="Edit the diagnostic axes used by the UIMM Boost questionnaire."
      />

      <main className="admin-axes-page-content">
        {message && <div className="toast-message">{message}</div>}

        <section className="admin-axes-toolbar">
          <div className="admin-axes-actions">
            <button className="secondary-button" onClick={goBackDashboard}>
              Back to dashboard
            </button>
          </div>
        </section>

        <section className="admin-axes-summary-grid">
          <div className="admin-axis-summary-card">
            <p>Total axes</p>
            <h3>{axes.length}</h3>
          </div>

          <div className="admin-axis-summary-card">
            <p>Active axes</p>
            <h3>{activeAxes.length}</h3>
          </div>

          <div className="admin-axis-summary-card">
            <p>Inactive axes</p>
            <h3>{inactiveAxes.length}</h3>
          </div>
        </section>

        <section className="admin-axes-list-section">
          <div className="admin-axes-list-header">
            <h2>Axes list</h2>
            <p>Click “Questions” to manage the questions for each axis.</p>
          </div>

          {axes.length === 0 ? (
            <div className="empty-card">
              <h3>No axes yet</h3>
              <p>No diagnostic axes are available.</p>
            </div>
          ) : (
            <div className="admin-axes-list">
              {axes
                .slice()
                .sort((a, b) => a.order_index - b.order_index)
                .map((axis) => (
                  <article key={axis.id} className="admin-axis-card">
                    <div className="admin-axis-order">
                      {axis.order_index}
                    </div>

                    <div className="admin-axis-main">
                      <div className="admin-axis-title-row">
                        <h3>{axis.name}</h3>

                        <span
                          className={
                            axis.is_active
                              ? "axis-status-badge active"
                              : "axis-status-badge inactive"
                          }
                        >
                          {axis.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <p>
                        {axis.description ||
                          "No description added for this axis."}
                      </p>
                    </div>

                    <div className="admin-axis-buttons">
                      <button
                        className="secondary-button"
                        onClick={() => openAxisQuestions(axis.id)}
                      >
                        Questions
                      </button>

                      <button
                        className="primary-button"
                        onClick={() => openEditModal(axis)}
                      >
                        Edit
                      </button>
                    </div>
                  </article>
                ))}
            </div>
          )}
        </section>
      </main>

      {editingAxis && (
        <div className="modal-overlay">
          <div className="company-modal">
            <div className="modal-header">
              <div>
                <h2>Edit axis</h2>
                <p>Update axis information.</p>
              </div>

              <button className="modal-close-button" onClick={closeEditModal}>
                ×
              </button>
            </div>

            <form className="company-create-form" onSubmit={saveEditingAxis}>
              <div className="form-grid-two">
                <div className="form-group">
                  <label>Axis name</label>
                  <input
                    type="text"
                    value={editingAxis.name}
                    onChange={(event) =>
                      updateEditingAxis("name", event.target.value)
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Order</label>
                  <input
                    type="number"
                    min="1"
                    value={editingAxis.order_index}
                    onChange={(event) =>
                      updateEditingAxis("order_index", event.target.value)
                    }
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  rows="4"
                  value={editingAxis.description}
                  onChange={(event) =>
                    updateEditingAxis("description", event.target.value)
                  }
                />
              </div>

              <label className="admin-axis-checkbox">
                <input
                  type="checkbox"
                  checked={editingAxis.is_active}
                  onChange={(event) =>
                    updateEditingAxis("is_active", event.target.checked)
                  }
                />
                <span>Active axis</span>
              </label>
              

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeEditModal}
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

export default AdminAxesPage;
