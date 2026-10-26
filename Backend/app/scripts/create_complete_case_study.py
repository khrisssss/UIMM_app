"""Preview or create one fully answered six-axis fictional case study."""
import argparse
import json
from app.database import SessionLocal
from app.services.complete_case_service import create_complete_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        summary = create_complete_case(db, apply=args.apply)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
