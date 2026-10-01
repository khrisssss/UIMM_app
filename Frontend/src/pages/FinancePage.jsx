import { useEffect, useState } from "react";
import api from "../api/api";
import AppHeader from "../components/AppHeader";
import "../App.css";
import "../styles/forms.css";

const fields = [
  ["revenue", "Chiffre d'affaires (CA)"], ["ebitda", "Excédent brut d'exploitation (EBE)"],
  ["operating_result", "Résultat d'exploitation (REX)"], ["net_result", "Résultat net"],
  ["depreciation", "Amortissements"], ["cash_flow", "Capacité d'autofinancement (CAF)"],
  ["equity", "Fonds propres"], ["gross_debt", "Endettement"],
  ["gross_cash", "Trésorerie brute"], ["factoring", "Affacturage"],
  ["total_assets", "Total bilan"], ["capex", "Investissements (CAPEX)"],
  ["debt_repayments", "Annuités de dette"],
];
const empty = () => ({ year: new Date().getFullYear(), kind: "actual", notes: "", ...Object.fromEntries(fields.map(([key]) => [key, ""])) });
const euro = (number) => number == null ? "—" : new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(number);
const fieldLabel = Object.fromEntries(fields);

function normalizeAmount(raw, label) {
  const value = String(raw ?? "").trim();
  if (!value) return null;
  // Accept French spacing and decimal commas, including pasted euro values.
  const compact = value.replace(/[\s\u00a0\u202f€]/g, "");
  let normalized = compact;
  if (compact.includes(",") && compact.includes(".")) {
    const decimalSeparator = compact.lastIndexOf(",") > compact.lastIndexOf(".") ? "," : ".";
    const thousandsSeparator = decimalSeparator === "," ? "." : ",";
    normalized = compact.replaceAll(thousandsSeparator, "").replace(decimalSeparator, ".");
  } else if ((compact.match(/[.,]/g) || []).length > 1) {
    const separator = compact.includes(",") ? "," : ".";
    const parts = compact.split(separator);
    normalized = parts.at(-1).length <= 2
      ? parts.slice(0, -1).join("") + "." + parts.at(-1)
      : parts.join("");
  } else {
    normalized = compact.replace(",", ".");
  }
  if (!/^[+-]?(?:\d+)(?:\.\d+)?$/.test(normalized)) {
    throw new Error(`Saisissez un montant valide pour ${label} (par exemple 2400000 ou 2 400 000,50).`);
  }
  return normalized;
}

function financeError(error) {
  if (error?.response?.status === 422) {
    const detail = error.response.data?.detail;
    if (Array.isArray(detail)) {
      return detail.map(item => {
        const field = item.loc?.at(-1);
        return `${fieldLabel[field] || field || "Champ"}: ${item.msg}`;
      }).join(" · ");
    }
    if (typeof detail === "string") return detail;
  }
  return error?.message || error?.response?.data?.detail || "Impossible d’enregistrer les données.";
}

export default function FinancePage() {
  const companyId = window.location.pathname.split("/")[2];
  const [company, setCompany] = useState(null);
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(empty());
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  async function refresh() {
    try {
      const [c, r] = await Promise.all([api.get(`/companies/${companyId}`), api.get(`/companies/${companyId}/financial-years`)]);
      setCompany(c.data); setRows(r.data);
    } catch (error) { setMessage(error?.response?.data?.detail || "Impossible de charger les données financières."); }
  }
  useEffect(() => { refresh(); }, [companyId]);
  async function save(event) {
    event.preventDefault(); setSaving(true); setMessage("");
    try {
      const payload = { ...form, year: Number(form.year) };
      for (const [key, label] of fields) payload[key] = normalizeAmount(form[key], label);
      await api.put(`/companies/${companyId}/financial-years/${payload.year}/${payload.kind}`, payload);
      setMessage("Données de l’année financière enregistrées."); setForm(empty()); await refresh();
    } catch (error) { setMessage(financeError(error)); }
    finally { setSaving(false); }
  }
  async function remove(row) {
    if (!window.confirm(`Supprimer les données ${row.kind === "actual" ? "réalisées" : "prévisionnelles"} de ${row.year} ?`)) return;
    try { await api.delete(`/companies/${companyId}/financial-years/${row.year}/${row.kind}`); await refresh(); }
    catch (error) { setMessage(error?.response?.data?.detail || "Impossible de supprimer les données."); }
  }
  return <div className="app-page">
    <AppHeader title={company?.name || "Finance"} />
    <div style={{ padding: "20px 24px 0", textAlign: "left" }}>
      <button className="secondary-button" onClick={() => window.location.href = `/companies/${companyId}/analysis`}>Voir le radar / SWOT</button>
    </div>
    <main className="questionnaire-page-content" style={{ maxWidth: 1100, margin: "auto", padding: 24 }}>
      {message && <p role="status">{message}</p>}
      {rows.length > 0 && <div style={{ overflowX: "auto" }}><table><thead><tr><th>Année</th><th>Type</th><th>CA</th><th>EBE</th><th>REX</th><th>CAF</th><th>Dette nette</th><th>CAPEX</th><th /></tr></thead>
      <tbody>{rows.map(row => <tr key={`${row.year}-${row.kind}`}><td>{row.year}</td><td>{row.kind === "actual" ? "Réalisé" : "Prévisionnel"}</td><td>{euro(row.revenue)}</td><td>{euro(row.ebitda)}</td><td>{euro(row.operating_result)}</td><td>{euro(row.cash_flow)}</td><td>{row.gross_debt == null || row.gross_cash == null ? "—" : euro(Number(row.gross_debt) - Number(row.gross_cash) + Number(row.factoring || 0))}</td><td>{euro(row.capex)}</td><td><button type="button" onClick={() => setForm({ ...empty(), ...Object.fromEntries(Object.entries(row).map(([k,v]) => [k, v ?? ""])) })}>Modifier</button><button type="button" onClick={() => remove(row)}>Supprimer</button></td></tr>)}</tbody></table></div>}
      <form onSubmit={save}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 32, marginBottom: 20 }}>
          <div className="form-group" style={{ minWidth: 180, margin: 0 }}><label style={{ display: "flex", flexDirection: "column", gap: 8 }}>Année<input type="number" min="1900" max="2200" required value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} /></label></div>
          <div className="form-group" style={{ minWidth: 180, margin: 0 }}><label style={{ display: "flex", flexDirection: "column", gap: 8 }}>Type<select value={form.kind} onChange={e => setForm({ ...form, kind: e.target.value })}><option value="actual">Réalisé</option><option value="forecast">Prévisionnel</option></select></label></div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          {fields.map(([key,label]) => <div className="form-group" key={key}><label>{label} (€)<input type="text" inputMode="decimal" value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} /></label></div>)}
        </div>
        <div className="form-group"><label>Notes <textarea maxLength="2000" rows={5} style={{ width: "100%", boxSizing: "border-box", minHeight: 120 }} value={form.notes || ""} onChange={e => setForm({ ...form, notes: e.target.value })} /></label></div>
        <button className="primary-button" disabled={saving}>{saving ? "Enregistrement en cours…" : "Enregistrer"}</button>
      </form>
    </main>
  </div>;
}
