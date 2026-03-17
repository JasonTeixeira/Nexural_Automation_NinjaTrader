from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def data_raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_exports(self) -> Path:
        return self.root / "data" / "exports"

    @property
    def data_processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def experiments(self) -> Path:
        return self.root / "experiments"

    @property
    def experiments_runs(self) -> Path:
        return self.root / "experiments" / "runs"

    @property
    def configs(self) -> Path:
        return self.root / "configs"


def get_project_root() -> Path:
    """Infer project root as the folder containing pyproject.toml."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    # fallback: assume repo root is two levels above src/utils
    return here.parents[3]


def paths() -> ProjectPaths:
    root = get_project_root()
    return ProjectPaths(root=root)
