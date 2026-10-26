"""Preview or import 20 sourced public company profiles around Toulouse."""
import argparse
import json
from app.database import SessionLocal
from app.services.public_company_import_service import import_public_companies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write profiles; default is read-only preview')
    args = parser.parse_args()
    with SessionLocal() as db:
        with db.begin():
            result = import_public_companies(db, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
