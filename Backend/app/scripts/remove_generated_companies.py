"""Remove generated company data and its public-research question, preserving other companies."""
import argparse
import json
from app.database import SessionLocal
from app.services.generated_data_cleanup_service import cleanup_generated_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Back up and delete; default previews only')
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        result = cleanup_generated_data(db, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
