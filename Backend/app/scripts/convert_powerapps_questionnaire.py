"""Read complete PowerFx records without evaluating the supplied formula."""
import argparse
import json
import re
from pathlib import Path

STRING = r'"(?:[^"\n]|"")*"'
VALUE = rf'(?:{STRING}(?:\s*&\s*(?:Char\(10\)|{STRING}))*)|true|false|\d+'
FIELD = re.compile(rf'([A-Za-z_][\w]*):\s*({VALUE})', re.DOTALL)


def convert(source):
    records = []
    # Braces in quoted strings are ignored. The last collection in the supplied
    # export lacks its closing parenthesis; every question record is complete.
    pattern = re.compile(r'\{((?:' + STRING + r'|[^{}"])+)\}', re.DOTALL)
    for match in pattern.finditer(source):
        record = {}
        for field in FIELD.finditer(match.group(1)):
            key, value = field.groups()
            if value.startswith('"'):
                tokens = re.findall(STRING + r'|Char\(10\)', value)
                record[key] = ''.join('\n' if t == 'Char(10)' else t[1:-1].replace('""', '"') for t in tokens)
            elif value in ('true', 'false'):
                record[key] = value == 'true'
            else:
                record[key] = int(value)
        if record.get('QuestionID', 0) > 0:
            records.append(record)
    ids = [r['QuestionID'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate source question IDs')
    if not records:
        raise ValueError('No complete question records found')
    for r in records:
        for key in ('QuestionID', 'Ordre'):
            if key not in r:
                raise ValueError(f'Missing {key}: {r}')
        if 'Axe' in r:
            if not (r.get('Question') or r.get('Enjeu')):
                raise ValueError(f'Missing question text: {r}')
        elif not (r.get('Section') and r.get('Question')):
            raise ValueError(f'Invalid profile question: {r}')
    return {'version': 1, 'source': 'User-provided Power Apps questionnaire export', 'questions': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(convert(args.source.read_text(encoding='utf-8')), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
