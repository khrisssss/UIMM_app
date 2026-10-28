"""Add generated comments to the existing company; preview and roll back by default."""
import argparse
import json
from app.database import SessionLocal
from app.services.montelac_comments_service import fill_montelac_comments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--company-id', type=int, default=102)
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            result = fill_montelac_comments(db, company_id=args.company_id)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise
    result['apply'] = args.apply
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
