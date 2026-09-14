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
      setMessage("Failed to load scores");
      console.error(error);
    }
  }

  useEffect(() => {
    loadScoresData();
  }, []);

  function getAxisName(axisId) {
    const axis = axes.find((item) => item.id === axisId);

    if (!axis) {
      return `Axis ${axisId}`;
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
        title="Scores and radar"
        subtitle="Review axis scores before generating the SWOT."
      />

      <button onClick={goBack}>Back to company</button>

      {message && <p>{message}</p>}

      {company && (
        <div>
          <h2>{company.name}</h2>
          <p>
            <strong>Status:</strong> {company.status}
          </p>
        </div>
      )}

      <hr />

      {scores.length === 0 ? (
        <p>No scores calculated yet.</p>
      ) : (
        <>
          <h3>Radar chart</h3>

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

          <h3>Score details</h3>

          <table border="1" cellPadding="8">
            <thead>
              <tr>
                <th>Axis</th>
                <th>Total</th>
                <th>Max</th>
                <th>Percentage</th>
                <th>Answered</th>
                <th>Total questions</th>
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