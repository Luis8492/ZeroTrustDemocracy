from pathlib import Path
import os
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
    config_path = _resolve_global_config_path()
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data or {}


def load(municipality: str):
    if municipality not in _ALLOWED_MUNICIPALITIES:
        raise ValueError(f"Unsupported municipality: {municipality}")
    config_path = _resolve_municipality_config_path(municipality)
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    data = data or {}

    root_dir = _resolve_path_root(config_path)
    # resolve paths relative to repo root
    for key in ['db_path', 'pii_dir', 'party_table_path']:
        if key in data:
            data[key] = str((root_dir / data[key]).resolve())

    if 'pii_files' in data:
        data['pii_files'] = [str((root_dir / p).resolve()) for p in data['pii_files']]

    return data


def _resolve_global_config_path() -> Path:
    config_path_env = os.getenv('CONFIG_PATH')
    candidates = []
    if config_path_env:
        candidates.append(Path(config_path_env).expanduser())

    config_dir_env = os.getenv('CONFIG_DIR')
    if config_dir_env:
        candidates.append(Path(config_dir_env).expanduser() / 'config.yaml')

    candidates.append(base_dir / 'config.yaml')

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def _resolve_municipality_config_path(municipality: str) -> Path:
    config_dir_env = os.getenv('CONFIG_DIR')
    if config_dir_env:
        config_dir = Path(config_dir_env).expanduser()
        candidates = [
            config_dir / f'{municipality}.yaml',
            config_dir / municipality / f'{municipality}.yaml',
            config_dir / municipality / 'config' / f'{municipality}.yaml',
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

    return municipal_dir / municipality / 'config' / f'{municipality}.yaml'


def _resolve_path_root(config_path: Path) -> Path:
    config_dir_env = os.getenv('CONFIG_DIR')
    if config_dir_env:
        config_dir = Path(config_dir_env).expanduser().resolve()
        config_path_resolved = config_path.resolve()
        try:
            config_path_resolved.relative_to(config_dir)
            return config_dir
        except ValueError:
            pass

    return base_dir
