from dataclasses import dataclass
from pathlib import Path


@dataclass
class CombineFactorTableResult:
    # result_matrix: "list[dict[str, int]]"
    result_matrix: "list[CombineFactorElement]"
    combination_formula: str


@dataclass
class CombineFactorElement:
    factor_name: str
    layer_name: str
    layer_path: Path
    layer_id: str

    @staticmethod
    def from_string(values: "list[str]"):
        return CombineFactorElement(
            factor_name=values[0],
            layer_name=values[1],
            layer_path=Path(values[2]),
            layer_id=values[3],
        )

    @staticmethod
    def to_string(combine_factor) -> "list[str]":
        return [
            combine_factor.factor_name,
            combine_factor.layer_name,
            str(combine_factor.layer_path),
            combine_factor.layer_id,
        ]
