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
      setMessage("Impossible de charger les utilisateurs.");
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
      setMessage("Le nom complet, l’identifiant et le mot de passe sont obligatoires.");
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

      setMessage("Utilisateur créé");

      setNewUser({
        full_name: "",
        username: "",
        password: "",
        role: "consultant",
        is_active: true,
      });

      loadUsers();
    } catch (error) {
      setMessage("Impossible de créer l’utilisateur.");
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

      setMessage("Utilisateur enregistré");
      loadUsers();
    } catch (error) {
      setMessage("Impossible de enregistrer l’utilisateur.");
      console.error(error);
    }
  }

  async function deactivateUser(userId) {
    try {
      await api.patch(`/users/${userId}/deactivate`);
      setMessage("Utilisateur désactivé");
      loadUsers();
    } catch (error) {
      setMessage("Impossible de désactiver l’utilisateur.");
      console.error(error);
    }
  }

  async function activateUser(userId) {
    try {
      await api.patch(`/users/${userId}/activate`);
      setMessage("Utilisateur activé");
      loadUsers();
    } catch (error) {
      setMessage("Impossible de activer l’utilisateur.");
      console.error(error);
    }
  }

  function goBack() {
    window.location.href = "/dashboard";
  }

  async function deleteUser(userId) {
    const confirmDelete = window.confirm(
      "Voulez-vous supprimer définitivement cet utilisateur ?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await api.delete(`/users/${userId}`);

      setMessage("Utilisateur supprimé.");
      loadUsers();
    } catch (error) {
      setMessage(getErrorMessage(error, "Impossible de supprimer l’utilisateur."));
      console.error(error);
    }
  }

  return (
    <div className="app-page">
      <AppHeader title="Utilisateurs" subtitle="Créez des utilisateurs et gérez leurs accès" />
      <main className="admin-users-content">
        <div className="admin-users-top-actions">
          <button className="secondary-button" onClick={goBack}>Retour au tableau de bord</button>
        </div>

        {message && <p role="status">{message}</p>}

        <div className="admin-users-layout">
          <section className="admin-users-card" aria-labelledby="create-user-title">
            <div className="admin-users-card-header">
              <h2 id="create-user-title">Créer un utilisateur</h2>
            </div>
            <form className="admin-users-form" onSubmit={createUser}>
              <div className="form-group">
                <label htmlFor="new-user-name">Nom complet</label>
                <input id="new-user-name" value={newUser.full_name}
                  onChange={(event) => updateNewUser("full_name", event.target.value)}
                  placeholder="Exemple : Bob Dupont" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-username">Identifiant</label>
                <input id="new-user-username" value={newUser.username}
                  onChange={(event) => updateNewUser("username", event.target.value)}
                  placeholder="Exemple : bob.dupont" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-password">Mot de passe</label>
                <input id="new-user-password" type="password" autoComplete="new-password"
                  value={newUser.password}
                  onChange={(event) => updateNewUser("password", event.target.value)}
                  placeholder="Mot de passe temporaire" />
              </div>
              <div className="form-group">
                <label htmlFor="new-user-role">Rôle</label>
                <select id="new-user-role" value={newUser.role}
                  onChange={(event) => updateNewUser("role", event.target.value)}>
                  <option value="consultant">Consultant</option>
                  <option value="admin">Administrateur</option>
                </select>
              </div>
              <label className="admin-users-checkbox-row">
                <input type="checkbox" checked={newUser.is_active}
                  onChange={(event) => updateNewUser("is_active", event.target.checked)} />Actif</label>
              <button className="primary-button" type="submit">Créer un utilisateur</button>
            </form>
          </section>

          <section className="admin-users-card" aria-labelledby="existing-users-title">
            <div className="admin-users-card-header">
              <h2 id="existing-users-title">Utilisateurs existants</h2>
            </div>
            <div className="admin-users-list">
              {users.length === 0 ? <p>Aucun utilisateur pour le moment.</p> : users.map((user) => (
                <article className="admin-user-item" key={user.id}>
                  <div className="admin-user-item-header">
                    <h3>#{user.id} — {user.full_name}</h3>
                    <span className={`user-status-badge ${user.is_active ? "user-status-active" : "user-status-inactive"}`}>
                      {user.is_active ? "Actif" : "Inactif"}
                    </span>
                  </div>
                  <div className="admin-user-edit-grid">
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-name`}>Nom complet</label>
                      <input id={`user-${user.id}-name`} value={user.full_name}
                        onChange={(event) => updateUser(user.id, "full_name", event.target.value)} />
                    </div>
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-username`}>Identifiant</label>
                      <input id={`user-${user.id}-username`} value={user.username}
                        onChange={(event) => updateUser(user.id, "username", event.target.value)} />
                    </div>
                    <div className="form-group">
                      <label htmlFor={`user-${user.id}-role`}>Rôle</label>
                      <select id={`user-${user.id}-role`} value={user.role}
                        onChange={(event) => updateUser(user.id, "role", event.target.value)}>
                        <option value="consultant">Consultant</option>
                        <option value="admin">Administrateur</option>
                      </select>
                    </div>
                    <label className="admin-users-checkbox-row">
                      <input type="checkbox" checked={user.is_active}
                        onChange={(event) => updateUser(user.id, "is_active", event.target.checked)} />Actif</label>
                  </div>
                  <div className="admin-user-actions">
                    <button className="primary-button" onClick={() => saveUser(user)}>Enregistrer l’utilisateur</button>
                    {user.is_active ? (
                      <button className="danger-button" onClick={() => deactivateUser(user.id)}>Désactiver</button>
                    ) : (
                      <>
                        <button className="secondary-button" onClick={() => activateUser(user.id)}>Activer</button>
                        <button className="danger-outline-button" onClick={() => deleteUser(user.id)}>Supprimer</button>
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
