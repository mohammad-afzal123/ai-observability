import pandas as pd

from services.prometheus_client import query_prometheus


def analyze_restarts():

    query = 'kube_pod_container_status_restarts_total'

    result = query_prometheus(query)

    data = result["data"]["result"]

    rows = []

    for item in data:

        pod = item["metric"].get("pod", "unknown")

        value = float(item["value"][1])

        rows.append({
            "pod": pod,
            "restarts": value
        })

    df = pd.DataFrame(rows)

    return df.to_dict(orient="records")
