# Remove generated company data and the public-research question

This command implements the requested cleanup. It identifies generated samples/case studies by their persistent synthetic flag or the known seeding markers. It identifies imported public profiles by the importer-created profile-answer comment or public-profile note. It does not delete a company simply because its name matches a catalog entry: manually entered companies and their records are preserved.

It removes the targeted companies and their linked diagnostic answers, profile answers, scores, SWOTs, reports, axis selections and financial-year records. It also deletes **Présentation de l’entreprise — recherche documentaire publique** and all answers to that specific question. The other profile questions and six-axis questionnaires remain configured.

Before any deletion, it writes a private JSON backup of the targeted records to the backend's persistent `generated_reports/cleanup_backups` directory. A backup failure aborts deletion. All database deletions are one transaction. Existing model files and report files on disk are not deleted by this command; their removed database report records no longer appear in the application.

After the cleanup helper has deployed, run on the VPS:

```bash
cd ~/UIMM_app
docker compose --env-file .env.production -f compose.production.yml exec -T backend python -m app.scripts.remove_generated_companies --apply
```

Omit `--apply` for a read-only inventory. No cleanup runs during deployment. The output lists targeted companies, deleted record counts and the backup path. Refresh the company list and profile questionnaire after successful execution. Running the cleanup again is harmless when nothing remains.

The old import/seed commands are not automatic; do not rerun them if these records should remain removed.
