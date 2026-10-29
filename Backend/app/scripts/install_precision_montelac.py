"""Add the requested axis questions and Précision Montelac; preview by default."""
import argparse
import json
from app.database import SessionLocal
from app.services.montelac_import_service import install_montelac


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Commit the questions, company, answers and scores')
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            result = install_montelac(db)
            result['apply'] = args.apply
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
