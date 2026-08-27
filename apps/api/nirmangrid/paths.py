from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "prompts").is_dir() and (parent / "data").is_dir():
            return parent
    return here.parents[3]
