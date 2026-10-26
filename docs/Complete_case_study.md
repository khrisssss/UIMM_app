# One complete questionnaire case: Atelier Métal Garonne

The company is named **Atelier Métal Garonne**, without a demonstration prefix. It is an entirely fictional pedagogical case; this provenance is visible in its notes, response comments and the Analyse screen. It is not an assessment of an actual company with that name.

The scenario describes a 28-person precision-machining workshop with seven CNC machines, quality/traceability capabilities and incomplete commercial, HR and digital processes. It provides a consistent source for generated profile answers, questionnaire responses and varied maturity scores. The scenario also contains a diversification opportunity (a fictional energy-maintenance tender) and external threats (a fictional customer forecast reduction and material price increase), so the SWOT has contextual evidence beyond an address and activity label. All figures, events and certifications in the scenario are invented case assumptions.

## What is created

- One non-archived company with size 11–50 and all six diagnostic axes selected.
- Detailed generated text answers, score codes and score values for every active axis question applicable to that company size.
- A generated answer for every active profile question in an active profile section.
- Six axis score records calculated from the actual inserted answers, using the same denominator and integer percentage rounding as the application.
- A starting orange state as part of the fictional scenario. No model is trained and no SWOT is generated automatically.

RSE questions with three bullet statements identify which statements the fictional response assumes satisfied, matching the chosen numeric score. Custom profile questions outside the known questionnaire receive a general case-context answer and may need editorial review. These are authored scenario responses, not company-supplied ground truth.

The data template is in `Backend/app/data/complete_case_study.json`. Changing the template does not overwrite an already-created company; repeat runs preserve existing records, including manual edits.

## Create it on the VPS

Merge the PR and wait for the backend/frontend deployment. Preview if desired:

```bash
cd ~/UIMM_app
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.create_complete_case_study
```

Create the complete case:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.create_complete_case_study --apply
```

The command inserts the entire case in a single transaction, never replaces an existing company with the same normalized name, and reports the company ID, number of profile/axis answers and calculated percentages. It requires the six active axes, applicable questions and scoring levels already configured. Existing real companies and their public-profile SWOTs remain untouched.

Then refresh Entreprises, open **Atelier Métal Garonne → Diagnostic** to inspect its populated questionnaires, and open **Analyse** to see the radar and click **Générer le SWOT**. The normal Azure generation flow now receives the detailed scenario, answered questions and six scores. Review the generated conclusions before using the case in a presentation.

## Provenance and training

The company carries a persistent `is_synthetic` database flag, exposed read-only in the company response schema. The real-data model dataset excludes it even if its name or notes change. Its default non-archived status also keeps it out of archived training examples. Creating this single case is not a claim of real-world model validation.

Deployment adds the provenance column without deleting records, marks the existing known seeded prefixes as synthetic, and keeps legacy name recognition for compatibility. Existing demo seeding writes this flag for new examples. Users cannot remove it through ordinary company create/update API fields.

## Validation

Tests cover read-only preview, all applicable question/profile responses, score totals/maxima/percentages, complete SWOT evidence, repeat-run preservation, existing-name collisions, missing-question errors, persistent provenance after renaming and standalone model registration. The full backend suite and frontend build run in GitHub Actions.
