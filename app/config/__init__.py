from pathlib import Path
import yaml


def load_config(name: str) -> dict:
    """Load configuration for the given municipality.

    Parameters
    ----------
    name: str
        Name of the municipality. The function will look for a YAML file
        located at ``config/<name>.yml`` relative to the project root.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    root = Path(__file__).resolve().parent.parent.parent
    config_file = root / "config" / f"{name}.yml"
    with config_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
