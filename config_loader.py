from pathlib import Path
import os
import yaml

base_dir = Path(__file__).resolve().parent
municipal_dir = base_dir / 'app' / 'municipal_modules'


def available_municipalities() -> set[str]:
    """Discover municipality modules at runtime.

    A municipality is "available" when its bundled YAML config exists at
    ``app/municipal_modules/<name>/config/<name>.yaml`` OR when a YAML by the
    same name exists under ``CONFIG_DIR``. This avoids hard-coded allowlists,
    so adding/removing a municipality module is the only edit required.
    """
    names: set[str] = set()
    if municipal_dir.exists():
        for d in municipal_dir.iterdir():
            if d.is_dir() and (d / 'config' / f'{d.name}.yaml').exists():
                names.add(d.name)

    config_dir_env = os.getenv('CONFIG_DIR')
    if config_dir_env:
        config_dir = Path(config_dir_env).expanduser()
        if config_dir.exists():
            for path in config_dir.glob('*.yaml'):
                if path.stem != 'config':
                    names.add(path.stem)
    return names


def load_global() -> dict:
    """Load global application configuration."""
    config_path = _resolve_global_config_path()
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data or {}


def load(municipality: str):
    if municipality not in available_municipalities():
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


def load_for_fetcher(municipality: str, fetcher_name: str) -> dict:
    """Return shared config merged with per-fetcher overrides.

    The unified YAML keeps shared fields (db_path, pii_files, party_table_path)
    at the top level and per-session overrides under ``fetchers.<FETCHER_NAME>``.
    Components that operate on a single session (the fetcher itself, the
    analyzer when picking encoding) want a flat dict, so this helper merges
    the two.
    """
    data = load(municipality)
    fetchers = data.get('fetchers') or {}
    overrides = fetchers.get(fetcher_name) or {}
    merged = {k: v for k, v in data.items() if k != 'fetchers'}
    merged.update(overrides)
    return merged


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
