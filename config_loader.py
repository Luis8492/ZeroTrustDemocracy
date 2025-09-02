from pathlib import Path
import yaml

base_dir = Path(__file__).resolve().parent
municipal_dir = base_dir / 'app' / 'municipal_modules'
# Municipalities correspond to subdirectories under `app/municipal_modules`
_ALLOWED_MUNICIPALITIES = {
    d.name
    for d in municipal_dir.iterdir()
    if (d / 'config' / f'{d.name}.yaml').exists()
}


def load_global() -> dict:
    """Load global application configuration."""
    config_path = base_dir / 'config.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data or {}


def load(municipality: str):
    if municipality not in _ALLOWED_MUNICIPALITIES:
        raise ValueError(f"Unsupported municipality: {municipality}")
    config_path = municipal_dir / municipality / 'config' / f'{municipality}.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # resolve paths relative to repo root
    for key in ['db_path', 'pii_dir', 'party_table_path']:
        if key in data:
            data[key] = str((base_dir / data[key]).resolve())

    if 'pii_files' in data:
        data['pii_files'] = [str((base_dir / p).resolve()) for p in data['pii_files']]

    return data
