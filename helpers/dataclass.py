from dataclasses import dataclass
from pathlib import Path


@dataclass
class CombineFactorTableResult:
    result_matrix: str
    combination_formula: str


@dataclass
class CombineFactorElement:
    factor_name: str
    layer_name: str
    layer_path: Path
