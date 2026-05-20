from agents.kubernetes_agent_utils import metric_results, metric_value


WATCHED_CONDITIONS = {
    "Ready",
    "MemoryPressure",
    "DiskPressure",
    "PIDPressure",
    "NetworkUnavailable"
}


def analyze_nodes():
    condition_query = 'kube_node_status_condition{condition=~"Ready|MemoryPressure|DiskPressure|PIDPressure|NetworkUnavailable",status="true"}'

    rows = []

    for item in metric_results(condition_query):
        metric = item.get("metric", {})
        condition = metric.get("condition", "Unknown")

        if condition not in WATCHED_CONDITIONS:
            continue

        node = metric.get("node", "unknown")
        active = metric_value(item)

        rows.append({
            "node": node,
            "condition": condition,
            "value": active,
            "severity": node_condition_severity(condition, active),
            "insight": node_condition_insight(node, condition, active)
        })

    return rows


def node_condition_severity(condition, active):
    if condition == "Ready" and active == 1:
        return "normal"

    if condition in ["MemoryPressure", "DiskPressure", "PIDPressure", "NetworkUnavailable"] and active == 1:
        return "critical"

    return "warning"


def node_condition_insight(node, condition, active):
    if condition == "Ready" and active == 1:
        return f"Node {node} is ready."

    if condition == "MemoryPressure":
        return f"Node {node} is reporting memory pressure."

    if condition == "DiskPressure":
        return f"Node {node} is reporting disk pressure."

    if condition == "PIDPressure":
        return f"Node {node} is reporting PID pressure."

    if condition == "NetworkUnavailable":
        return f"Node {node} network is unavailable."

    return f"Node {node} condition {condition} is active."
