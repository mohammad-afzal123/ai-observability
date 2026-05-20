from agents.kubernetes_agent_utils import metric_name, metric_results, metric_value


def analyze_readiness():
    ready_query = 'kube_pod_status_ready{condition="true"}'

    rows = []

    for item in metric_results(ready_query):
        pod = metric_name(item, "pod")
        namespace = metric_name(item, "namespace")
        ready = metric_value(item)

        rows.append({
            "pod": pod,
            "namespace": namespace,
            "ready": ready,
            "value": ready,
            "status": "Ready" if ready == 1 else "Not Ready",
            "insight": readiness_insight(pod, namespace, ready)
        })

    return rows


def readiness_insight(pod, namespace, ready):
    if ready == 1:
        return f"Pod {pod} in {namespace} is ready to serve traffic."

    return f"Pod {pod} in {namespace} is not ready; inspect probes, image pulls, or dependencies."
