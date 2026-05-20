import pandas as pd

from services.prometheus_client import query_prometheus
from services.anomaly_detector import detect_anomalies


def analyze_memory():

    query = 'container_memory_usage_bytes'

    result = query_prometheus(query)

    data = result["data"]["result"]

    rows = []

    for item in data:

        pod = item["metric"].get("pod", "unknown")
        namespace = item["metric"].get("namespace", "default")

        value = float(item["value"][1])

        rows.append({
            "pod": pod,
            "namespace": namespace,
            "value": value
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return []

    df = detect_anomalies(df)

    return df.to_dict(orient="records")
