# Generate SWOT drafts for the 20 public company profiles

The existing SWOT screen can generate from company-profile information even without diagnostic scores. This update makes that path explicit and adds a batch command for the imported public profiles.

The AI receives the sourced profile, selected axes and available company comments. Unanswered axes are excluded from the score payload: missing responses are not low maturity scores. In public-profile mode, the default RSE boolean is unknown, and the prompt distinguishes published activity/capability statements from a consultant's completed diagnostic. Unsupported SWOT categories can remain empty. Draft findings are marked as public-information findings and are saved with source `public_sources_ai` and status `draft`. No questionnaire response, score, company state or model-training label is created or modified.

The Analyse screen labels this result as **Pré-analyse documentaire**, does not recalculate scores for unassessed public profiles, and hides score rows with no answered questions. An actually answered zero score remains valid and visible. The normal questionnaire-based SWOT generation path still works.

## One company from the application

Open Entreprises → select a public company → Analyse → **Générer la pré-analyse SWOT**. This uses the existing Azure OpenAI configuration. Review the draft before saving/validating it. Missing evidence should remain missing; a complete-looking four-quadrant diagram is not evidence of a real company interview.

## Batch generation on the VPS

After merge and successful backend/frontend deployment, preview:

```bash
cd ~/UIMM_app
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.generate_public_company_swots
```

To generate all eligible profiles:

```bash
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.generate_public_company_swots --apply
```

Preview performs no AI call and no write. Apply makes one Azure OpenAI request per eligible company, using the credentials already configured in the backend. Progress is printed while the command runs. Each successful draft is committed separately; errors are reported per company and the process exits with a non-zero status if any fail. A retry preserves already saved drafts and attempts the remaining eligible companies.

The batch only considers catalog companies with an imported public-profile answer and an unassessed state. It skips assessed companies, companies with diagnostic evidence, and every company that already has a company-wide SWOT, including manually written or validated SWOTs. It never replaces existing findings. The regular UI generation button retains its normal explicit regeneration behavior.

## Validation

Tests check the 20-company preview and creation flow with a fake AI dependency, metadata and text-column persistence, absence of invented answers/scores, preservation of existing manual SWOTs, invalid AI-output rollback, exclusion of unanswered axes, preservation of answered zero scores, and standalone model registration without API credentials. Real Azure output must be reviewed in the deployed application; automated tests do not claim to validate its business conclusions.
