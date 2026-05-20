import pandas as pd

from services.anomaly_detector import detect_anomalies
from services.prometheus_client import query_prometheus


def metric_results(query):
    result = query_prometheus(query)
    return result.get("data", {}).get("result", [])


def metric_name(item, *keys):
    metric = item.get("metric", {})

    for key in keys:
        value = metric.get(key)
        if value:
            return value

    return "unknown"


def metric_value(item):
    return float(item.get("value", [0, 0])[1])


def apply_value_anomalies(rows):
    df = pd.DataFrame(rows)

    if df.empty or len(df.index) < 2:
        return rows

    return detect_anomalies(df).to_dict(orient="records")
