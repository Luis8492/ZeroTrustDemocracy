from pathlib import Path
import yaml

base_dir = Path(__file__).resolve().parent
_ALLOWED_MUNICIPALITIES = {p.stem for p in (base_dir / 'config').glob('*.yaml')}


def load(municipality: str):
    if municipality not in _ALLOWED_MUNICIPALITIES:
        raise ValueError(f"Unsupported municipality: {municipality}")
    config_path = base_dir / 'config' / f'{municipality}.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # resolve paths relative to repo root
    for key in ['db_path', 'pii_dir', 'party_table_path']:
        if key in data:
            data[key] = str((base_dir / data[key]).resolve())

    if 'pii_files' in data:
        data['pii_files'] = [str((base_dir / p).resolve()) for p in data['pii_files']]

    return data
