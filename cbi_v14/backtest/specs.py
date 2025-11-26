from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class DatasetSpec:
    """Specification of a training dataset slice used in a backtest."""

    name: str
    bq_table: str
    symbol: str
    horizon: str
    train_start: str
    train_end: str
    val_start: Optional[str] = None
    val_end: Optional[str] = None
    test_start: Optional[str] = None
    test_end: Optional[str] = None


@dataclass
class ModelSpec:
    """Specification of a model configuration used in a backtest."""

    name: str
    algorithm: str
    target_col: str
    feature_cols: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Captured metrics from a single backtest run."""

    metrics_train: Dict[str, Any]
    metrics_val: Optional[Dict[str, Any]] = None
    metrics_test: Optional[Dict[str, Any]] = None
    top_features: Optional[List[Dict[str, Any]]] = None


@dataclass
class BacktestRun:
    """
    Aggregate record for a backtest: dataset, model, results, and provenance.

    This is intended as a simple container that can be serialized to JSON
    alongside saved models for audit and comparison.
    """

    dataset: DatasetSpec
    model: ModelSpec
    result: BacktestResult
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    code_version: Optional[str] = None  # e.g. git SHA
    notes: Optional[str] = None

