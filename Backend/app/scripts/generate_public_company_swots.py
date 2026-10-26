"""Preview or generate SWOT drafts for the imported Toulouse public profiles."""
import argparse
import json
import sys
from app.database import SessionLocal
from app.services.public_swot_service import plan_public_swots, create_public_swot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Call Azure OpenAI and save drafts; default is preview only')
    args = parser.parse_args()
    with SessionLocal() as db:
        plan = plan_public_swots(db)
    result = {'apply': args.apply, 'eligible_count': len(plan['eligible']), 'eligible': plan['eligible'], 'skipped': plan['skipped'], 'created': [], 'failed': []}
    if args.apply:
        for index, company in enumerate(plan['eligible'], 1):
            print(f"SWOT {index}/{len(plan['eligible'])} : {company['name']}", file=sys.stderr, flush=True)
            try:
                # Save each successful company independently so a retry skips it.
                with SessionLocal.begin() as db:
                    record = create_public_swot(db, company['company_id'])
                    saved = {**company, 'swot_id': record.id}
                result['created'].append(saved)
            except Exception as error:
                result['failed'].append({**company, 'error': str(error)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
