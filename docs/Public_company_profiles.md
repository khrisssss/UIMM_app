# Import 20 real company profiles around Toulouse

This catalog contains real company/establishment profiles researched from public company websites, official registries and local-government directories on 26 October 2026. The JSON includes each profile's name, local address, activity summary, source URLs and research date. Some records describe a local site or a group rather than an independently verified legal entity; these are identified in their names. No relationship with UIMM, company interview or completed diagnostic is implied.

| Company / local establishment | Town |
| --- | --- |
| Mecaprotec Industries | Muret |
| Dedienne Aerospace | Toulouse |
| Liebherr-Aerospace Toulouse | Toulouse |
| HEMERIA | Toulouse |
| COMAT | Flourens |
| EREMS | Flourens |
| Anywaves | Toulouse |
| Infinite Orbits | Toulouse |
| Loft Orbital | Toulouse |
| Exotrail | Toulouse |
| ACTIA Automotive | Toulouse |
| Latecoere | Toulouse |
| ATR | Blagnac |
| SAS Cauquil | Mondouzil |
| Mecachrome Toulouse | Launaguet |
| SOGECLAIR | Blagnac |
| Ateliers de la Haute-Garonne | Flourens |
| Airbus — site de Saint-Martin-du-Touch | Toulouse |
| Thales Alenia Space France — Toulouse | Toulouse |
| ARÉA — mobilier urbain | Flourens |

All sources are recorded in `Backend/app/data/toulouse_companies_public.json`, and copied to each new profile so they remain visible in the application. Addresses may be public mailing addresses. Exotrail's entry uses only the publicly confirmed town rather than guessing a street address.

## What the import creates

For each new company: the public name/address/activity summary, a visible general comment with sources, a sourced answer to the shared profile question **Présentation de l’entreprise — recherche documentaire publique**, and six selected diagnostic axes. The other existing profile and axis questionnaires are available through the normal application screens but remain unanswered.

Names do not have a DEMO prefix because the companies are real. Their state is **Non évalué** (`unassessed`, shown in grey), status is Prospect (an application workflow default), and they are not archived. Size, personal contacts, interview dates, scores and internal management practices are not invented. The existing RSE boolean retains its application default; it is not a verified statement about the company's RSE policy. RSE is preselected as a diagnostic area to complete, not as an assertion of maturity. The notes identify these internal fields as awaiting confirmation.

The importer never inserts scored axis answers, model training labels, completed diagnostics or scores. These records cannot be used as completed training examples until genuine responses are supplied, a consultant assigns a supported state, and the normal training eligibility checks are met. Public profile research alone is not model-evaluation evidence.

## Run on the VPS after merge/deployment

From `~/UIMM_app`, preview first:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.import_toulouse_companies
```

Review the reported new/existing company names, then import:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.import_toulouse_companies --apply
```

The import runs in a single transaction and does not run at startup/deployment. Re-running it skips existing companies matched by normalized names or the explicit aliases in the catalog. Existing addresses, comments, contacts, labels, answers and scores are never overwritten. Multiple matches stop the import for review. Run this command one at a time; the existing database does not enforce unique company names.

On a local installation, run the equivalent `python -m app.scripts.import_toulouse_companies` commands from Backend with the database configured.

No questionnaires, demo data or models need to be regenerated. Refresh the company list after applying the import. Adding public profiles does not remove or change existing fictional company records or convert their generated answers into genuine responses.
