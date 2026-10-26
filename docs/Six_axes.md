# Six diagnostic axes

The application now uses Stratégie, Performance, Marketing, RH, Digitalisation and RSE. Finance is retired from axis selection, diagnostics, questionnaire administration, radar scores and comparisons, new SWOT/report inputs and PowerPoint axis pages. The standalone Finance form and financial-year API routes are no longer exposed. The company profile's Finances section and its three questions are inactive and hidden.

On backend startup, an idempotent transaction deactivates any existing Finance/Finances axis, its questions, categories and scoring scales, and clears its company-selection and portfolio-display flags. It also deactivates the Finances profile section and its questions. Existing primary keys, financial years, answers, scores and saved documents are preserved for history and read-only company exports. New score calculations preserve retired historical scores while excluding them from current results. Previously saved report/SWOT text is historical and is not rewritten: regenerate SWOT and reports when a current six-axis version is needed.

The axis seed now creates six axes. The original Power Apps export is retained as source documentation; the importer includes its 216 axis questions and 20 non-financial profile questions (236 total) and never reimports its three Finance profile questions.

## Deployment

Merge the PR after checks pass. The existing GitHub Actions deployment rebuilds the backend and frontend. The backend applies retirement on startup; no database deletion or extra import command is needed. Refresh the browser after deployment.

If deploying manually on the VPS after merging:

```bash
cd ~/UIMM_app
git pull --ff-only origin feature/finance-axis-years
docker compose --env-file .env.production -f compose.production.yml up -d --build backend frontend
```

Check six axes in the administration screen, that Finance is absent from a company's axis selection and diagnostic, and that the radar contains only the selected remaining axes. The old Finance URL is no longer a form route.

## Prediction model

The input schema is now six axis percentages plus three company-size indicators (nine features). A model trained with the previous seven-axis schema cannot be reused. New real and demo bundles use separate six-axis filenames and retain the existing distinction between real and fictional records. Retrain the appropriate mode through the administrator dashboard; existing companies and their responses do not need to be recreated. Previous evaluation JSON files remain evidence of their original seven-axis experiment, not evaluations of this new model.

## Validation

Regression tests use historical Finance records to check repeatable retirement without data loss; six-axis selection and diagnostic endpoints; current and archive-average radar scores; preservation of stored Finance scores during recalculation; exclusion from profile and AI/PPT contexts; and the nine-feature model schema. The existing model pipeline, importer and standalone seed tests continue to run in CI.
