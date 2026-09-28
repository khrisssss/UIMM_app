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
    } catch (error) { setMessage(error?.response?.data?.detail || "Unable to load financial data."); }
  }
  useEffect(() => { refresh(); }, [companyId]);
  async function save(event) {
    event.preventDefault(); setSaving(true); setMessage("");
    try {
      const payload = { ...form, year: Number(form.year) };
      for (const [key] of fields) payload[key] = form[key] === "" ? null : form[key];
      await api.put(`/companies/${companyId}/financial-years/${payload.year}/${payload.kind}`, payload);
      setMessage("Financial year saved."); setForm(empty()); await refresh();
    } catch (error) { setMessage(error?.response?.data?.detail || "Unable to save."); }
    finally { setSaving(false); }
  }
  async function remove(row) {
    if (!window.confirm(`Delete ${row.kind} ${row.year}?`)) return;
    try { await api.delete(`/companies/${companyId}/financial-years/${row.year}/${row.kind}`); await refresh(); }
    catch (error) { setMessage(error?.response?.data?.detail || "Unable to delete."); }
  }
  return <div className="app-page">
    <AppHeader title={company?.name || "Finance"} subtitle="Finance — historical figures and projections" />
    <main className="questionnaire-page-content" style={{ maxWidth: 1100, margin: "auto", padding: 24 }}>
      <button className="secondary-button" onClick={() => window.location.href = `/companies/${companyId}/diagnostic`}>Back to diagnostic</button>
      {message && <p role="status">{message}</p>}
      <h2>Financial years</h2>
      {rows.length > 0 && <div style={{ overflowX: "auto" }}><table><thead><tr><th>Year</th><th>Type</th><th>CA</th><th>EBE</th><th>REX</th><th>CAF</th><th>Net debt</th><th>CAPEX</th><th /></tr></thead>
      <tbody>{rows.map(row => <tr key={`${row.year}-${row.kind}`}><td>{row.year}</td><td>{row.kind === "actual" ? "Actual" : "Forecast"}</td><td>{euro(row.revenue)}</td><td>{euro(row.ebitda)}</td><td>{euro(row.operating_result)}</td><td>{euro(row.cash_flow)}</td><td>{row.gross_debt == null || row.gross_cash == null ? "—" : euro(Number(row.gross_debt) - Number(row.gross_cash) + Number(row.factoring || 0))}</td><td>{euro(row.capex)}</td><td><button type="button" onClick={() => setForm({ ...empty(), ...Object.fromEntries(Object.entries(row).map(([k,v]) => [k, v ?? ""])) })}>Edit</button><button type="button" onClick={() => remove(row)}>Delete</button></td></tr>)}</tbody></table></div>}
      <h2>Add or edit a financial year</h2>
      <form onSubmit={save}>
        <div className="form-group"><label>Year <input type="number" min="1900" max="2200" required value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} /></label></div>
        <div className="form-group"><label>Type <select value={form.kind} onChange={e => setForm({ ...form, kind: e.target.value })}><option value="actual">Actual</option><option value="forecast">Forecast</option></select></label></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          {fields.map(([key,label]) => <div className="form-group" key={key}><label>{label} (€)<input type="text" inputMode="decimal" value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} /></label></div>)}
        </div>
        <div className="form-group"><label>Notes <textarea maxLength="2000" rows={5} style={{ width: "100%", boxSizing: "border-box", minHeight: 120 }} value={form.notes || ""} onChange={e => setForm({ ...form, notes: e.target.value })} /></label></div>
        <button className="primary-button" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
      </form>
    </main>
  </div>;
}
