import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import AppHeader from "../components/AppHeader";

import api from "../api/api";

function ScoresPage() {
  const { companyId } = useParams();

  const [company, setCompany] = useState(null);
  const [axes, setAxes] = useState([]);
  const [scores, setScores] = useState([]);
  const [message, setMessage] = useState("");

  async function loadScoresData() {
    try {
      const companyResponse = await api.get(`/companies/${companyId}`);
      setCompany(companyResponse.data);

      const axesResponse = await api.get("/axes/");
      setAxes(axesResponse.data);

      const scoresResponse = await api.get(`/companies/${companyId}/scores`);
      setScores(scoresResponse.data);
    } catch (error) {
      setMessage("Impossible de charger les scores.");
      console.error(error);
    }
  }

  useEffect(() => {
    loadScoresData();
  }, []);

  function getAxisName(axisId) {
    const axis = axes.find((item) => item.id === axisId);

    if (!axis) {
      return `Axe ${axisId}`;
    }

    return axis.name;
  }

  const radarData = scores.map((score) => ({
    axis: getAxisName(score.axis_id),
    percentage: score.score_percentage,
  }));

  function goBack() {
    window.location.href = `/companies/${companyId}`;
  }

  return (
    <div>
      <h1>Scores</h1>
      <AppHeader
        title="Scores et radar"
        subtitle="Vérifiez les scores par axe avant de générer le SWOT."
      />

      <button onClick={goBack}>Retour à l’entreprise</button>

      {message && <p>{message}</p>}

      {company && (
        <div>
          <h2>{company.name}</h2>
          <p>
            <strong>Statut :</strong> {company.status}
          </p>
        </div>
      )}

      <hr />

      {scores.length === 0 ? (
        <p>Aucun score calculé pour le moment.</p>
      ) : (
        <>
          <h3>Graphique radar</h3>

          <div style={{ width: "100%", height: 400 }}>
            <ResponsiveContainer>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="axis" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Score"
                  dataKey="percentage"
                  stroke="#2563eb"
                  fill="#2563eb"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <h3>Détail des scores</h3>

          <table border="1" cellPadding="8">
            <thead>
              <tr>
                <th>Axe</th>
                <th>Total</th>
                <th>Maximum</th>
                <th>Pourcentage</th>
                <th>Réponses</th>
                <th>Nombre total de questions</th>
              </tr>
            </thead>

            <tbody>
              {scores.map((score) => (
                <tr key={score.id}>
                  <td>{getAxisName(score.axis_id)}</td>
                  <td>{score.score_total}</td>
                  <td>{score.score_max}</td>
                  <td>{score.score_percentage}%</td>
                  <td>{score.answered_questions}</td>
                  <td>{score.total_questions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default ScoresPage;