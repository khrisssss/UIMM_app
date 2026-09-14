import { useEffect, useState } from "react";
import AppHeader from "../components/AppHeader";
import api from "../api/api";
import "../App.css";
import "../styles/forms.css";
import "../styles/admin-users.css";

function getErrorMessage(error, fallbackMessage) {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallbackMessage;
}

function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState("");

  const [newUser, setNewUser] = useState({
    full_name: "",
    username: "",
    password: "",
    role: "consultant",
    is_active: true,
  });

  async function loadUsers() {
    try {
      const response = await api.get("/users/");
      setUsers(response.data);
    } catch (error) {
      setMessage("Failed to load users");
      console.error(error);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  function updateNewUser(field, value) {
    setNewUser((previousUser) => ({
      ...previousUser,
      [field]: value,
    }));
  }

  function updateUser(userId, field, value) {
    setUsers((previousUsers) =>
      previousUsers.map((user) =>
        user.id === userId
          ? {
              ...user,
              [field]: value,
            }
          : user
      )
    );
  }

  async function createUser(event) {
    event.preventDefault();

    if (!newUser.full_name || !newUser.username || !newUser.password) {
      setMessage("Full name, username, and password are required.");
      return;
    }

    try {
      await api.post("/users/", {
        full_name: newUser.full_name,
        username: newUser.username,
        password: newUser.password,
        role: newUser.role,
        is_active: newUser.is_active,
      });

      setMessage("User created");

      setNewUser({
        full_name: "",
        username: "",
        password: "",
        role: "consultant",
        is_active: true,
      });

      loadUsers();
    } catch (error) {
      setMessage("Failed to create user");
      console.error(error);
    }
  }

  async function saveUser(user) {
    try {
      await api.patch(`/users/${user.id}`, {
        full_name: user.full_name,
        username: user.username,
        role: user.role,
        is_active: user.is_active,
      });

      setMessage("User saved");
      loadUsers();
    } catch (error) {
      setMessage("Failed to save user");
      console.error(error);
    }
  }

  async function deactivateUser(userId) {
    try {
      await api.patch(`/users/${userId}/deactivate`);
      setMessage("User deactivated");
      loadUsers();
    } catch (error) {
      setMessage("Failed to deactivate user");
      console.error(error);
    }
  }

  async function activateUser(userId) {
    try {
      await api.patch(`/users/${userId}/activate`);
      setMessage("User activated");
      loadUsers();
    } catch (error) {
      setMessage("Failed to activate user");
      console.error(error);
    }
  }

  function goBack() {
    window.location.href = "/dashboard";
  }

  async function deleteUser(userId) {
    const confirmDelete = window.confirm(
      "Are you sure you want to permanently delete this user?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await api.delete(`/users/${userId}`);

      setMessage("User deleted successfully.");
      loadUsers();
    } catch (error) {
      setMessage(getErrorMessage(error, "Failed to delete user."));
      console.error(error);
    }
  }

  return (
    <div className="app-page">
      <AppHeader title="Users" subtitle="Create new users and manage their access" />
      <main className="admin-users-content">
        <div className="admin-users-top-actions">
          <button className="secondary-button" onClick={goBack}>Back to dashboard</button>
        </div>

        {message && <p role="status">{message}</p>}

        <div className="admin-users-layout">
          <section className="admin-users-card" aria-labelledby="create-user-title">
            <div className="admin-users-card-header">
              <h2 id="create-user-title">Create user</h2>
            </div>
            <form className="admin-users-form" onSubmit={createUser}>
              <div className="form-group">
                <label htmlFor="new-user-name">Full name</label>
                <input id="new-user-name" value={newUser.full_name}
                  onChange={(event) => updateNewUser("full_name", event.target.value)}
                  placeholder="Example: Jema Sucgang" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-username">Username</label>
                <input id="new-user-username" value={newUser.username}
                  onChange={(event) => updateNewUser("username", event.target.value)}
                  placeholder="Example: jema.sucgang" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-password">Password</label>
                <input id="new-user-password" type="password" autoComplete="new-password"
                  value={newUser.password}
                  onChange={(event) => updateNewUser("password", event.target.value)}
                  placeholder="Temporary password" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-role">Role</label>
                <select id="new-user-role" value={newUser.role}
                  onChange={(event) => updateNewUser("role", event.target.value)}>
                  <option value="consultant">Consultant</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <label className="admin-users-checkbox-row">
                <input type="checkbox" checked={newUser.is_active}
                  onChange={(event) => updateNewUser("is_active", event.target.checked)} />
                Active
              </label>
              <button className="primary-button" type="submit">Create user</button>
            </form>
          </section>

          <section className="admin-users-card" aria-labelledby="existing-users-title">
            <div className="admin-users-card-header">
              <h2 id="existing-users-title">Existing users</h2>
            </div>
            <div className="admin-users-list">
              {users.length === 0 ? <p>No users yet.</p> : users.map((user) => (
                <article className="admin-user-item" key={user.id}>
                  <div className="admin-user-item-header">
                    <h3>#{user.id} — {user.full_name}</h3>
                    <span className={`user-status-badge ${user.is_active ? "user-status-active" : "user-status-inactive"}`}>
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="admin-user-edit-grid">
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-name`}>Full name</label>
                      <input id={`user-${user.id}-name`} value={user.full_name}
                        onChange={(event) => updateUser(user.id, "full_name", event.target.value)} />
                    </div>
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-username`}>Username</label>
                      <input id={`user-${user.id}-username`} value={user.username}
                        onChange={(event) => updateUser(user.id, "username", event.target.value)} />
                    </div>
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-role`}>Role</label>
                      <select id={`user-${user.id}-role`} value={user.role}
                        onChange={(event) => updateUser(user.id, "role", event.target.value)}>
                        <option value="consultant">Consultant</option>
                        <option value="admin">Admin</option>
                      </select>
                    </div>
                    <label className="admin-users-checkbox-row">
                      <input type="checkbox" checked={user.is_active}
                        onChange={(event) => updateUser(user.id, "is_active", event.target.checked)} />
                      Active
                    </label>
                  </div>
                  <div className="admin-user-actions">
                    <button className="primary-button" onClick={() => saveUser(user)}>Save user</button>
                    {user.is_active ? (
                      <button className="danger-button" onClick={() => deactivateUser(user.id)}>Deactivate</button>
                    ) : (
                      <>
                        <button className="secondary-button" onClick={() => activateUser(user.id)}>Activate</button>
                        <button className="danger-outline-button" onClick={() => deleteUser(user.id)}>Delete</button>
                      </>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default AdminUsersPage;
