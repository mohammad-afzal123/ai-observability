from agents.kubernetes_agent_utils import apply_value_anomalies, metric_name, metric_results, metric_value


def analyze_network():
    receive_query = 'sum by (pod, namespace) (rate(container_network_receive_bytes_total{pod!=""}[5m]))'
    transmit_query = 'sum by (pod, namespace) (rate(container_network_transmit_bytes_total{pod!=""}[5m]))'

    pods = {}

    for item in metric_results(receive_query):
        pod = metric_name(item, "pod")
        namespace = metric_name(item, "namespace")
        key = f"{namespace}/{pod}"
        pods.setdefault(key, {"pod": pod, "namespace": namespace, "receive_bps": 0, "transmit_bps": 0})
        pods[key]["receive_bps"] = metric_value(item)

    for item in metric_results(transmit_query):
        pod = metric_name(item, "pod")
        namespace = metric_name(item, "namespace")
        key = f"{namespace}/{pod}"
        pods.setdefault(key, {"pod": pod, "namespace": namespace, "receive_bps": 0, "transmit_bps": 0})
        pods[key]["transmit_bps"] = metric_value(item)

    rows = []

    for key, values in pods.items():
        total_bps = values["receive_bps"] + values["transmit_bps"]
        values["value"] = total_bps
        values["anomaly"] = 0
        values["insight"] = network_insight(values["pod"], values["receive_bps"], values["transmit_bps"])
        rows.append(values)

    return apply_value_anomalies(rows)


def network_insight(pod, receive_bps, transmit_bps):
    if receive_bps + transmit_bps == 0:
        return f"Pod {pod} is not currently reporting network traffic."

    if transmit_bps > receive_bps * 2:
        return f"Pod {pod} is transmit-heavy; check egress pressure or downstream calls."

    if receive_bps > transmit_bps * 2:
        return f"Pod {pod} is receive-heavy; check inbound load and service fan-in."

    return f"Pod {pod} has balanced network traffic."
