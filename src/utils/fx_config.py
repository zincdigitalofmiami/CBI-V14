#!/usr/bin/env python3
"""
FX configuration helpers for CBI-V14.

Inspired by gs-quant's FX defaults, but scoped to the FX instruments
and futures you actually use (DataBento + FRED).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FxInstrument:
    """Canonical definition of an FX rate or future."""

    name: str  # e.g. "BRLUSD"
    base: str  # currency in numerator
    quote: str  # currency in denominator
    source: str  # e.g. "databento", "fred"
    symbol: str  # local symbol / file prefix, e.g. "6l", "dexchus"


class FxConfig:
    """Central registry of FX instruments used in CBI-V14."""

    def __init__(self) -> None:
        instruments: List[FxInstrument] = [
            # DataBento CME FX futures
            FxInstrument(name="BRLUSD", base="BRL", quote="USD", source="databento", symbol="6l"),
            FxInstrument(name="EURUSD", base="EUR", quote="USD", source="databento", symbol="6e"),
            FxInstrument(name="JPYUSD", base="JPY", quote="USD", source="databento", symbol="6j"),
            FxInstrument(name="CADUSD", base="CAD", quote="USD", source="databento", symbol="6c"),
            FxInstrument(name="GBPUSD", base="GBP", quote="USD", source="databento", symbol="6b"),
            FxInstrument(name="AUDUSD", base="AUD", quote="USD", source="databento", symbol="6a"),
            FxInstrument(name="CNHUSD", base="CNH", quote="USD", source="databento", symbol="cnh"),
            # FRED spot series (examples from FX_CALCULATIONS_REQUIRED.md)
            FxInstrument(name="CNYUSD", base="CNY", quote="USD", source="fred", symbol="dexchus"),
            FxInstrument(name="BRLUSD_FRED", base="BRL", quote="USD", source="fred", symbol="dexbzus"),
            FxInstrument(name="EURUSD_FRED", base="EUR", quote="USD", source="fred", symbol="dexuseu"),
            FxInstrument(name="JPYUSD_FRED", base="JPY", quote="USD", source="fred", symbol="dexjpus"),
        ]
        self._by_name: Dict[str, FxInstrument] = {fx.name: fx for fx in instruments}
        self._by_symbol: Dict[str, FxInstrument] = {fx.symbol: fx for fx in instruments}

    def by_name(self, name: str) -> Optional[FxInstrument]:
        return self._by_name.get(name)

    def by_symbol(self, symbol: str) -> Optional[FxInstrument]:
        return self._by_symbol.get(symbol.lower())

    def databento_symbols(self) -> List[str]:
        """Return local symbols for all DataBento FX futures."""
        return [fx.symbol for fx in self._by_name.values() if fx.source == "databento"]

    def fred_symbols(self) -> List[str]:
        """Return local symbols for all FRED FX series."""
        return [fx.symbol for fx in self._by_name.values() if fx.source == "fred"]


FX_CONFIG = FxConfig()
