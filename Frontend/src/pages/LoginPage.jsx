import { useState } from "react";

import api from "../api/api";
import "../App.css";
import "../styles/forms.css";
import "../styles/login.css";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function handleLogin(event) {
    event.preventDefault();

    if (!username || !password) {
      setMessage("Veuillez saisir votre identifiant et votre mot de passe.");
      return;
    }

    try {
      const response = await api.post("/auth/login", {
        username: username,
        password: password,
      });

      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));

      if (response.data.user.role === "admin") {
        window.location.href = "/dashboard";
      } else {
        window.location.href = "/companies";
      }
    } catch (error) {
      setMessage("Identifiant ou mot de passe incorrect.");
      console.error(error);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card-header">
          <h2>Connexion à votre compte</h2>
          <p>Saisissez votre identifiant et votre mot de passe pour vous connecter.</p>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Identifiant</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {message && <p className="error-message">{message}</p>}

          <button type="submit" className="primary-button full-width">Se connecter</button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;