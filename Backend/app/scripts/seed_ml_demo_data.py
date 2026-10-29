"""Preview or explicitly insert fictional companies and their questionnaire answers."""
import argparse
import json
from app.database import SessionLocal
from app.services.ml_demo_data_service import seed_demo_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--per-class', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    with SessionLocal() as db:
        with db.begin():
            result = seed_demo_data(db, apply=args.apply, per_class=args.per_class, seed=args.seed)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
