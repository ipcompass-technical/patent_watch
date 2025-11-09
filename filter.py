import json
import re
from typing import List, Dict

SOFTWARE_PREFIXES = ['G06', 'H04L', 'G16H', 'G05B']


def load_patents(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_ipc_list(raw_ipc: str) -> List[str]:
    if not raw_ipc:
        return []
    # Remove colons and newlines, collapse whitespace
    cleaned = raw_ipc.replace(':', ' ').replace('\n', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Split on commas
    parts = [p.strip() for p in cleaned.split(',')]
    # Remove empty entries and normalize spacing/case
    codes = [p.upper().replace(' ', '') for p in parts if p]
    return codes


def classify_ipc_codes(ipc_codes: List[str]) -> str:
    software_count = 0
    other_count = 0

    for code in ipc_codes:
        if any(code.startswith(prefix) for prefix in SOFTWARE_PREFIXES):
            software_count += 1
        else:
            other_count += 1

    if software_count > 0 and other_count > 0:
        return 'Hybrid'
    if software_count > 0 and other_count == 0:
        return 'Software'
    return 'Non-Software'


def main() -> None:
    patents = load_patents('all_patents.json')
    classified_patents: List[Dict] = []

    for patent in patents:
        raw_ipc = patent.get('international_classification', '')
        ipc_codes = clean_ipc_list(raw_ipc)
        patent_type = classify_ipc_codes(ipc_codes)

        patent['ipc_codes'] = ipc_codes
        patent['patent_type'] = patent_type
        classified_patents.append(patent)

    with open('classified_patents.json', 'w', encoding='utf-8') as f:
        json.dump(classified_patents, f, indent=2, ensure_ascii=False)

    print(f"Classified {len(classified_patents)} patents → classified_patents.json")


if __name__ == '__main__':
    main()


