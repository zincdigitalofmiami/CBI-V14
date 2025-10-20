#!/usr/bin/env python3
"""
One-off ingestor for China soybean imports and South America harvest/planting alternative sources.
Numeric-only mode: extracts conservative numeric signals and loads to economic_indicators only.
"""
import re
import time
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple

import requests
from bs4 import BeautifulSoup  # type: ignore
from google.cloud import bigquery  # type: ignore

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

PROJECT_ID = "cbi-v14"


def http_get(url: str, timeout: int = 20) -> Optional[requests.Response]:
    headers = DEFAULT_HEADERS.copy()
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            time.sleep(1 + attempt * 2)
        except Exception:
            time.sleep(1 + attempt * 2)
    return None


def extract_numeric_imports(text: str) -> List[Tuple[float, str]]:
    results: List[Tuple[float, str]] = []
    text_norm = re.sub(r"\s+", " ", text.lower())
    for sentence in re.split(r"(?<=[\.!?])\s+", text_norm):
        if any(k in sentence for k in ["import", "imports"]) and any(k in sentence for k in ["million", "mmt"]):
            m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(million|mmt)", sentence)
            if m:
                val = float(m.group(1))
                unit = m.group(2)
                mmt = val  # treat both million and mmt as mmt scalar
                results.append((mmt, sentence.strip()[:280]))
    return results


def load_records(client: bigquery.Client, table_id: str, records: List[Dict]) -> Tuple[int, Optional[str]]:
    if not records:
        return 0, None
    try:
        table = client.get_table(table_id)
        schema_cols = [f.name for f in table.schema]
        aligned: List[Dict] = []
        for r in records:
            r_aligned = {k: (r[k] if k in r else None) for k in schema_cols}
            aligned.append(r_aligned)
        job = client.load_table_from_json(aligned, table, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"))
        job.result()
        return len(aligned), None
    except Exception as e:
        return 0, str(e)


def build_econ_record(indicator: str, value: float, source_name: str, url: str, notes: str, ts: Optional[datetime] = None, confidence: float = 0.6) -> Dict:
    return {
        "time": (ts or datetime.now(timezone.utc)),
        "indicator": indicator,
        "value": value,
        "source_name": source_name,
        "confidence_score": confidence,
        "provenance_uuid": str(uuid.uuid4()),
        "ingest_timestamp_utc": datetime.now(timezone.utc),
        "source_url": url,
        "notes": notes[:1000],
    }


def process_article_numeric_only(url: str, source_name: str, category: str, client: bigquery.Client) -> Dict:
    resp = http_get(url)
    result = {"url": url, "source": source_name, "numeric": 0, "error": None}
    if not resp:
        result["error"] = "fetch_failed"
        return result
    soup = BeautifulSoup(resp.content, "html.parser")
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    body_text = " ".join(paragraphs) or soup.get_text(separator=" ", strip=True)

    econ_records: List[Dict] = []
    numeric_hits = extract_numeric_imports(body_text)
    for mmt, snippet in numeric_hits:
        econ_records.append(
            build_econ_record(
                indicator=("cn_soy_imports_mmt" if category == "china_imports" else "sa_soy_metric"),
                value=mmt,
                source_name=source_name,
                url=url,
                notes=f"Extracted from text: {snippet}",
                confidence=0.55,
            )
        )

    econ_loaded, econ_err = load_records(client, f"{PROJECT_ID}.forecasting_data_warehouse.economic_indicators", econ_records)
    result["numeric"] = econ_loaded
    if econ_err:
        result["error"] = econ_err
    return result


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)

    china_links = [
        ("https://www.reuters.com/world/china/us-soybean-farmers-deserted-by-big-buyer-china-scramble-other-importers-2025-10-03/", "Reuters"),
        ("https://www.bloomberg.com/news/articles/2025-09-19/china-seeks-trade-edge-by-shunning-us-soy-in-first-since-1990s", "Bloomberg"),
        ("https://www.dtnpf.com/agriculture/web/ag/news/article/2025/09/29/china-soybean-users-see-breakthrough", "DTN_Progressive_Farmer"),
        ("https://www.agweb.com/news/crops/soybeans/8-soybeans-thats-reality-some-farmers-china-remains-absent-buying", "AgWeb"),
        ("https://farmaction.us/china-stopped-buying-u-s-soybeans-the-real-problem-started-decades-ago/", "FarmAction"),
        ("https://soygrowers.com/news-releases/soybeans-without-a-buyer-the-export-gap-hurting-u-s-farms/", "Soygrowers"),
    ]

    sa_links = [
        ("https://farmdocdaily.illinois.edu/2025/03/record-soybean-harvest-in-south-america-and-favorable-outlook-for-exports.html", "Farmdoc"),
        ("https://hedgepointglobal.com/en/blog/progress-of-corn-and-soybean-crops-in-brazil-and-argentina", "HedgepointGlobal"),
        ("https://ag.purdue.edu/commercialag/home/resource/2025/09/u-s-soybean-harvest-starts-with-no-sign-of-chinese-buying-as-brazil-sets-export-record/", "PurdueAg"),
        ("https://ocj.com/category/2024-2025-south-american-update/", "OCJ"),
    ]

    results = []

    for url, src in china_links:
        res = process_article_numeric_only(url, src, "china_imports", client)
        results.append(res)
        time.sleep(5)

    for url, src in sa_links:
        res = process_article_numeric_only(url, src, "sa_harvest", client)
        results.append(res)
        time.sleep(5)

    print(json.dumps({"ingestion_results": results}, default=str, indent=2))


if __name__ == "__main__":
    main()


