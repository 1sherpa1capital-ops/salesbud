from pathlib import Path


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent.parent.parent.parent / "data"


def get_browser_state_dir() -> Path:
    """Get the browser state directory path."""
    return get_data_dir() / "browser_state"


def get_db_path() -> Path:
    """Get the database file path."""
    return get_data_dir() / "salesbud.db"
