from agents.kubernetes_agent_utils import apply_value_anomalies, metric_name, metric_results, metric_value


def analyze_filesystem():
    usage_query = 'sum by (pod, namespace) (container_fs_usage_bytes{pod!=""})'
    limit_query = 'sum by (pod, namespace) (container_fs_limit_bytes{pod!=""})'

    pods = {}

    for item in metric_results(usage_query):
        pod = metric_name(item, "pod")
        namespace = metric_name(item, "namespace")
        key = f"{namespace}/{pod}"
        pods.setdefault(key, {"pod": pod, "namespace": namespace, "usage_bytes": 0, "limit_bytes": 0})
        pods[key]["usage_bytes"] = metric_value(item)

    for item in metric_results(limit_query):
        pod = metric_name(item, "pod")
        namespace = metric_name(item, "namespace")
        key = f"{namespace}/{pod}"
        pods.setdefault(key, {"pod": pod, "namespace": namespace, "usage_bytes": 0, "limit_bytes": 0})
        pods[key]["limit_bytes"] = metric_value(item)

    rows = []

    for key, values in pods.items():
        limit = values["limit_bytes"]
        usage = values["usage_bytes"]
        usage_percent = (usage / limit * 100) if limit else 0

        values["usage_percent"] = usage_percent
        values["value"] = usage_percent if usage_percent else usage
        values["anomaly"] = 0
        values["insight"] = filesystem_insight(values["pod"], usage_percent)
        rows.append(values)

    return apply_value_anomalies(rows)


def filesystem_insight(pod, usage_percent):
    if usage_percent >= 85:
        return f"Pod {pod} is close to filesystem pressure and may need cleanup or a larger volume."

    if usage_percent >= 65:
        return f"Pod {pod} has moderate filesystem usage; watch growth rate."

    return f"Pod {pod} filesystem usage is within the expected range."
