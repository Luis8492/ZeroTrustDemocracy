from pathlib import Path
import yaml

def load(municipality: str):
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / 'config' / f'{municipality}.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # resolve paths relative to repo root
    for key in ['db_path', 'pii_dir']:
        if key in data:
            data[key] = str((base_dir / data[key]).resolve())
    return data
