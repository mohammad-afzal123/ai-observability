from agents.kubernetes_agent_utils import metric_results, metric_value


def analyze_pod_phases():
    phase_query = 'kube_pod_status_phase{phase=~"Pending|Running|Succeeded|Failed|Unknown"}'

    rows = []

    for item in metric_results(phase_query):
        metric = item.get("metric", {})
        active = metric_value(item)

        if active != 1:
            continue

        pod = metric.get("pod", "unknown")
        namespace = metric.get("namespace", "unknown")
        phase = metric.get("phase", "Unknown")

        rows.append({
            "pod": pod,
            "namespace": namespace,
            "phase": phase,
            "value": active,
            "severity": phase_severity(phase),
            "insight": phase_insight(pod, namespace, phase)
        })

    return rows


def phase_severity(phase):
    if phase in ["Failed", "Unknown"]:
        return "critical"

    if phase == "Pending":
        return "warning"

    return "normal"


def phase_insight(pod, namespace, phase):
    if phase == "Running":
        return f"Pod {pod} in {namespace} is running."

    if phase == "Pending":
        return f"Pod {pod} in {namespace} is pending; check scheduling, images, or resource limits."

    if phase == "Failed":
        return f"Pod {pod} in {namespace} failed; inspect recent logs and restart policy."

    return f"Pod {pod} in {namespace} is in {phase} phase."
