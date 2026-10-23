# Power Apps questionnaires and C12 model tests

This change provides a repeatable questionnaire import, fictional completed diagnostics, an explicit demo training mode, and automated tests of the ML pipeline. It does not certify predictive quality on real companies or validate a competence on behalf of the assessor.

## What is imported

| Questionnaire | Questions |
| --- | ---: |
| Company profile | 23 |
| Stratégie | 26 |
| Performance | 40 |
| Marketing | 17 |
| RH | 58 |
| Digitalisation | 50 |
| RSE | 25 |
| **Total** | **239** |

The bank is in `Backend/app/data/powerapps_questionnaire.json`. Original Power Apps IDs, order, categories, size flags and question types remain in that file. They are not used as database primary keys. RSE retains the issue title and all three statements, with visible line breaks. Digitalisation uses Domaine as the displayed category. The ERP OuiNon profile question uses the application's existing text answer field: enter Oui or Non. No database schema migration is required.

The supplied file contains no new scored Finance questionnaire. Its three qualitative Finances profile questions are included. The existing financial-year form is unchanged. RH, RSE and Digitalisation omit size flags in the source; these questions default to all three sizes. The historical app calls its first size group `<10`, while the Power Apps source describes the first group as 1–10. The ML encoder accepts both strings in this same historical group; the boundary wording should be confirmed with UIMM before changing company categories.

Performance source IDs 2029 and 2030 have identical text in the same category. Both are preserved at their source order. Review whether both should remain active in the administration screen before using the rubric for real diagnostics.

## Import the bank

First merge the reviewed PR and let the existing CI/CD finish. No import or demo seed runs at startup or during deployment. On an existing local installation with its database configured, use:

```bash
cd ~/Documents/UIMM_app
git pull --ff-only origin feature/finance-axis-years
cd Backend
python -m app.scripts.import_powerapps_questionnaire
```

This previews the number of new and existing questions. The database must already contain the active axes and one active scoring scale per imported axis (normally created by the existing application initialization). The importer uses existing scale maxima; it does not reset scoring levels.

After reviewing the preview, insert and activate the new questions:

```bash
python -m app.scripts.import_powerapps_questionnaire --apply --activate
```

Without `--activate`, newly inserted questions stay inactive for administrator review. Later `--activate` only applies to newly inserted records; it never reactivates previously imported or manually deactivated questions. Activate those through Questions par axe / Profil de l’entreprise in the administration screen.

Existing question IDs, answers, text, order, visibility and scores are preserved. Re-running the unchanged bank does not insert it twice. Matching uses axis/section, category and normalized text; order distinguishes the two identical Performance source questions. Ambiguous existing duplicates stop the import rather than choosing a question arbitrarily. If you edit imported text/category/order and later re-import, review the preview: a changed question may be treated as new. The importer is additive, so older non-matching questions also remain. Review and deactivate obsolete questions manually before collecting comparable real training data. Activating extra questions changes the denominator when diagnostics are recalculated; historical totals are not recalculated by this script.

For the OVH Docker installation, run the equivalent commands from `~/UIMM_app`:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.import_powerapps_questionnaire
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.import_powerapps_questionnaire --apply --activate
```

Each applied import is one database transaction. An error rolls back its inserts. Run import commands one at a time.

## Add fictional diagnostics and train in the application

Preview and then create 20 companies per state, 60 total:

```bash
# From Backend, for the local installation:
python -m app.scripts.seed_ml_demo_data --per-class 20
python -m app.scripts.seed_ml_demo_data --apply --per-class 20
```

On OVH:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.seed_ml_demo_data --apply --per-class 20
```

The generator fills active questions applicable to company size, uses actual scoring-level codes, writes profile answers, and calculates axis scores from the generated answers. It does not invent scored Finance questions. Names start with `DEMO ML - ` and every diagnostic is marked as fictional in its comments. The companies are archived so completed examples are available for training; open the archived companies list to inspect them. Existing companies, including already generated examples, are left untouched on re-runs. Increasing `--per-class` adds new examples. The default seed is 42; existing examples are not rewritten when the seed changes.

As an administrator, open Tableau de bord → Prédiction de l’état de l’entreprise → Voir les détails. Check **Entraîner uniquement sur les entreprises fictives de démonstration**, then train. With a fresh 60-company seed, the split contains 45 training companies and 15 held-out test companies. Metrics show the dataset source, accuracy, macro F1 and confusion matrix. Download the evaluation JSON for the report. Open an archived demo company's Analyse page to try prediction; the result is visibly marked as a demo.

Demo and real model bundles have separate paths under `Backend/ml_artifacts` (inside Docker: `/app/ml_artifacts`). Model and metrics are saved together by an atomic file replacement. Demo training never replaces the real model, and real companies cannot use the demo model. The old model file from the previous implementation is not loaded by this version: retrain the real model when sufficient eligible real data is available. All names beginning with `DEMO` are reserved for fictional records, including legacy examples. Do not rename fictional companies to remove that prefix or use it for real customers; source separation currently uses this naming convention rather than a dedicated database provenance field.

## Real data and interpretation

Real mode no longer silently adds synthetic rows when data is insufficient. It requires at least 12 eligible archived diagnostics, at least two states, and at least four companies per represented state. Each stored axis score must describe a fully answered questionnaire. Zero scores are valid; duplicate score rows, unknown company sizes, missing/non-finite features and invalid score ranges are rejected. Consultants must review `general_state` before archiving: the database's default orange label is not an expert annotation, and archiving alone cannot verify label quality.

This version uses seven axis percentages and three company-size indicators. Missing axes still map to zero, as in the previous implementation. Keep the selected axes and rubric consistent when comparing companies; an explicit missing-axis strategy and questionnaire-version tracking remain future model improvements. Do not use the model's own suggestions as independent ground-truth labels. For a defensible real evaluation, collect independently reviewed examples of all relevant states and keep an additional untouched validation set when tuning the model. The fixed 25% holdout here verifies a single training run; repeated tuning against that holdout would bias the result.

Synthetic states are generated from simulated maturity profiles. A high demo score only confirms that the model can learn the generator's patterns. It is not evidence of real-world predictive accuracy, and adding more simulated companies does not solve that limitation.

## C12: tests and report evidence

Run tests locally from Backend (the test database is isolated SQLite, never PostgreSQL or customer data):

```bash
python -m pip install -r requirements-test.txt
python -m pytest tests/ -q --cov=app.services.company_state_ml_service --cov=app.services.questionnaire_import_service --cov=app.services.ml_demo_data_service --cov-report=term-missing --cov-report=xml --junitxml=test-results.xml
```

GitHub Actions runs the same command, alongside the frontend build. The seven financial-year schema tests remain, with additional tests covering:

| Test area | Evidence |
| --- | --- |
| Input quality | Missing columns, null/NaN/infinite values, invalid ranges, unknown labels/sizes, insufficient classes and duplicate company IDs are rejected before saving a model. |
| Preparation and split | Deterministic stratification, disjoint company IDs, and scaler statistics learned only from training rows. |
| Training and evaluation | Accuracy independently recomputed on the held-out rows, confusion-matrix totals, F1 bounds and valid probability sums. |
| Persistence and inference | Reload the saved model and its metrics, predict an actual seeded diagnostic, preserve its manually stored state. |
| Integration and source isolation | Import → seed answers → calculate scores → train → reload → predict; demo records excluded from real training and demo training cannot overwrite real artifacts. |
| Questionnaire integrity | Counts, complete RSE statements, source conversion, preview without writes, repeat import, preservation of existing answers and transaction rollback. |

For the competence report, retain the commit/PR, successful Actions run, pytest/coverage output, a screenshot of the labelled demo training screen, and the downloaded evaluation JSON. The JSON includes split IDs/counts, class counts, fixed seed, feature names, library versions, per-class precision/recall/F1, confusion matrix and dataset source. Report test coverage separately from predictive metrics: coverage measures exercised code, while holdout metrics measure predictions on that specific dataset.

Suggested wording, adapted to the run you actually perform:

> J’ai développé des tests automatisés couvrant la validation des données, la préparation, la séparation stratifiée apprentissage/test, l’entraînement, l’évaluation et le rechargement du modèle. Un test d’intégration exécute la chaîne complète depuis les questionnaires jusqu’à la prédiction sur des entreprises fictives. Les données de démonstration et les modèles correspondants sont séparés des données réelles. Les tests sont exécutés en intégration continue. Les métriques obtenues sur données synthétiques démontrent le fonctionnement du pipeline ; la qualité métier reste à évaluer sur des diagnostics réels annotés indépendamment.
