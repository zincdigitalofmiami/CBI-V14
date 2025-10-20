#!/usr/bin/env python3
"""
CONAB Soybean Harvest Ingestion

Pulls Brazil soybean area, production, and yield from CONAB public tab-delimited files
and writes aggregated indicators into forecasting_data_warehouse.economic_indicators.
"""

import json
import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import List, Dict

import pandas as pd
import requests
from google.cloud import bigquery

PROJECT_ID = "cbi-v14"
ECONOMIC_TABLE = f"{PROJECT_ID}.forecasting_data_warehouse.economic_indicators"
CONAB_SOURCES = {
    "LevantamentoGraos": "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/LevantamentoGraos.txt",
    "SerieHistoricaGraos": "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/SerieHistoricaGraos.txt",
}
SOY_KEYWORD = "SOJA"


def parse_conab_csv(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    content = response.content.decode("latin-1")
    df = pd.read_csv(StringIO(content), sep=";", dtype=str)
    return df


def clean_numeric(series: pd.Series) -> pd.Series:
    if series.dtype == object:
        return pd.to_numeric(series.str.replace(",", ".", regex=False), errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def parse_ag_year(ag_year: str) -> datetime:
    if not isinstance(ag_year, str):
        return datetime.now(timezone.utc)
    ag_year = ag_year.strip()
    if "/" in ag_year:
        start, end = ag_year.split("/", 1)
        try:
            start_year = int(start)
            end_year = int(start[:2] + end) if len(end) == 2 else int(end)
            # assign to 1 July of ending crop year (rough midpoint of marketing year)
            return datetime(end_year, 7, 1, tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        year = int(ag_year)
        return datetime(year, 7, 1, tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def aggregate_serie_historica(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["produto"].str.contains(SOY_KEYWORD, case=False, na=False)].copy()
    if df.empty:
        return df
    df["area_plantada_mil_ha"] = clean_numeric(df.get("area_plantada_mil_ha"))
    df["producao_mil_t"] = clean_numeric(df.get("producao_mil_t"))
    df["produtividade_mil_ha_mil_t"] = clean_numeric(df.get("produtividade_mil_ha_mil_t"))
    df = df.dropna(subset=["area_plantada_mil_ha", "producao_mil_t"])
    grouped = (
        df.groupby("ano_agricola", as_index=False)
        .agg(
            area_kha=("area_plantada_mil_ha", "sum"),
            production_kt=("producao_mil_t", "sum"),
        )
    )
    grouped["yield_t_per_ha"] = (
        grouped.apply(
            lambda row: row["production_kt"] * 1000 / (row["area_kha"] * 1000)
            if row["area_kha"] and row["area_kha"] > 0
            else None,
            axis=1,
        )
    )
    return grouped


def build_indicator_rows(grouped: pd.DataFrame, source_name: str, dataset_label: str) -> List[Dict]:
    rows: List[Dict] = []
    for _, record in grouped.iterrows():
        crop_year = str(record.get("ano_agricola", "")).strip()
        timestamp = parse_ag_year(crop_year)
        base_meta = {
            "time": timestamp.isoformat(),
            "source_name": source_name,
            "confidence_score": 0.8,
            "ingest_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "provenance_uuid": str(uuid.uuid4()),
        }
        area_value = record.get("area_kha")
        if pd.notna(area_value):
            rows.append(
                {
                    **base_meta,
                    "indicator": "br_soybean_area_kha",
                    "value": float(area_value),
                }
            )
        production_value = record.get("production_kt")
        if pd.notna(production_value):
            rows.append(
                {
                    **base_meta,
                    "indicator": "br_soybean_production_kt",
                    "value": float(production_value),
                }
            )
        yield_value = record.get("yield_t_per_ha")
        if pd.notna(yield_value):
            rows.append(
                {
                    **base_meta,
                    "indicator": "br_soybean_yield_t_per_ha",
                    "value": float(yield_value),
                }
            )
    return rows


def load_rows(client: bigquery.Client, table_id: str, rows: List[Dict]) -> int:
    if not rows:
        return 0
    job = client.load_table_from_json(rows, table_id, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"))
    job.result()
    return len(rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    total_rows = 0

    try:
        serie_hist = parse_conab_csv(CONAB_SOURCES["SerieHistoricaGraos"])
        grouped = aggregate_serie_historica(serie_hist)
        rows = build_indicator_rows(grouped, source_name="CONAB", dataset_label="SerieHistoricaGraos")
        loaded = load_rows(client, ECONOMIC_TABLE, rows)
        total_rows += loaded
        print(json.dumps({"dataset": "SerieHistoricaGraos", "rows_loaded": loaded}))
    except Exception as exc:  # pylint: disable=broad-except
        print(json.dumps({"dataset": "SerieHistoricaGraos", "error": str(exc)}))

    try:
        levantamento = parse_conab_csv(CONAB_SOURCES["LevantamentoGraos"])
        # For Levantamento, keep latest levantamento per crop year (higher id_levantamento)
        levantamento = levantamento[levantamento["produto"].str.contains(SOY_KEYWORD, case=False, na=False)].copy()
        levantamento["id_levantamento"] = pd.to_numeric(levantamento.get("id_levantamento"), errors="coerce")
        levantamento["area_plantada_mil_ha"] = clean_numeric(levantamento.get("area_plantada_mil_ha"))
        levantamento["producao_mil_t"] = clean_numeric(levantamento.get("producao_mil_t"))
        levantamento = levantamento.dropna(subset=["id_levantamento", "area_plantada_mil_ha", "producao_mil_t"])
        latest = (
            levantamento.sort_values("id_levantamento")
            .groupby("ano_agricola", as_index=False)
            .tail(1)
        )
        latest_grouped = latest.groupby("ano_agricola", as_index=False).agg(
            area_kha=("area_plantada_mil_ha", "sum"),
            production_kt=("producao_mil_t", "sum"),
        )
        latest_grouped["yield_t_per_ha"] = (
            latest_grouped.apply(
                lambda row: row["production_kt"] * 1000 / (row["area_kha"] * 1000)
                if row["area_kha"] and row["area_kha"] > 0
                else None,
                axis=1,
            )
        )
        rows = build_indicator_rows(latest_grouped, source_name="CONAB", dataset_label="LevantamentoGraos")
        loaded = load_rows(client, ECONOMIC_TABLE, rows)
        total_rows += loaded
        print(json.dumps({"dataset": "LevantamentoGraos", "rows_loaded": loaded}))
    except Exception as exc:  # pylint: disable=broad-except
        print(json.dumps({"dataset": "LevantamentoGraos", "error": str(exc)}))

    print(json.dumps({"total_rows_loaded": total_rows}))


if __name__ == "__main__":
    main()
