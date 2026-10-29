"""Preview the questionnaire import, or apply it explicitly in one transaction."""
import argparse
import json
from app.database import SessionLocal
from app.services.questionnaire_import_service import import_questionnaire


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write new records (default: preview only)')
    parser.add_argument('--activate', action='store_true', help='Make newly inserted questions visible immediately')
    args = parser.parse_args()
    if args.activate and not args.apply:
        parser.error('--activate requires --apply')
    with SessionLocal() as db:
        with db.begin():
            result = import_questionnaire(db, apply=args.apply, activate=args.activate)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
