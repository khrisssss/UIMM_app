"""Install Mécanique Solérive with French answers, comments and scores."""
import argparse
import json
from pathlib import Path
from app.database import SessionLocal
from app.services.montelac_import_service import install_answered_company

DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'mecanique_solerive.json'


def load_solerive():
    return json.loads(DATA_PATH.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Save the company, answers, comments and scores')
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            result = install_answered_company(db, load_solerive())
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
