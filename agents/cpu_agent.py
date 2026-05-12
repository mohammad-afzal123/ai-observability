import pandas as pd

from services.prometheus_client import query_prometheus
from services.anomaly_detector import detect_anomalies
from services.nlp_insights import generate_cpu_insight


def analyze_cpu():

    query = 'rate(container_cpu_usage_seconds_total[1m])'

    result = query_prometheus(query)

    data = result["data"]["result"]

    rows = []

    for item in data:

        pod = item["metric"].get("pod", "unknown")

        value = float(item["value"][1])

        rows.append({
            "pod": pod,
            "value": value
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return []

    # Detect anomalies
    df = detect_anomalies(df)

    # Generate NLP insights
    results = []

    for _, row in df.iterrows():

        insight = generate_cpu_insight(
            row["pod"],
            row["value"],
            row["anomaly"]
        )

        results.append({
            "pod": row["pod"],
            "value": row["value"],
            "anomaly": int(row["anomaly"]),
            "insight": insight
        })

    return results
