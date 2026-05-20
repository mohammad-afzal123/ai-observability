import subprocess
from agents.cpu_agent import analyze_cpu
from agents.filesystem_agent import analyze_filesystem
from agents.memory_agent import analyze_memory
from agents.network_agent import analyze_network
from agents.node_agent import analyze_nodes
from agents.phase_agent import analyze_pod_phases
from agents.readiness_agent import analyze_readiness
from agents.restart_agent import analyze_restarts
from services.remediation_executor import AUTO_REMEDIATE, execute_remediation_commands


DEFAULT_NAMESPACE = "default"


def analyze_remediation():
    issues = []

    issues.extend(cpu_remediations(safe_analyze("cpu", analyze_cpu)))
    issues.extend(memory_remediations(safe_analyze("memory", analyze_memory)))
    issues.extend(restart_remediations(safe_analyze("restart", analyze_restarts)))
    issues.extend(network_remediations(safe_analyze("network", analyze_network)))
    issues.extend(filesystem_remediations(safe_analyze("filesystem", analyze_filesystem)))
    issues.extend(readiness_remediations(safe_analyze("readiness", analyze_readiness)))
    issues.extend(phase_remediations(safe_analyze("phase", analyze_pod_phases)))
    issues.extend(node_remediations(safe_analyze("node", analyze_nodes)))

    actions = []

    for index, issue in enumerate(issues, start=1):
        action = build_action(index, issue)
        action["command_results"] = execute_remediation_commands(action["commands"])
        action["status"] = action_status(action["command_results"])
        action["timeline"] = build_timeline(action["status"])
        action["resolved"] = action["status"] in ["resolved", "ready"]
        actions.append(action)

    return {
        "auto_remediation_enabled": AUTO_REMEDIATE,
        "execution_mode": "automatic" if AUTO_REMEDIATE else "simulation",
        "active_issues": len([action for action in actions if not action["resolved"]]),
        "resolved_issues": len([action for action in actions if action["resolved"]]),
        "actions": actions
    }


def safe_analyze(agent_name, analyzer):
    try:
        return analyzer()
    except Exception as error:
        return [{
            "agent": agent_name,
            "error": str(error)
        }]


def cpu_remediations(rows):
    return [
        remediation(
            "CPU Agent",
            row.get("pod"),
            "High CPU anomaly detected",
            "Scale or restart the workload after marking it for investigation.",
            "warning",
            [
                annotate_pod(row.get("pod"), "observability.ai/cpu-remediation", "required", row.get("namespace")),
                rollout_restart(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if is_anomaly(row.get("anomaly"))
    ]


def memory_remediations(rows):
    return [
        remediation(
            "Memory Agent",
            row.get("pod"),
            "Memory pressure anomaly detected",
            "Restart the owning workload to clear leak pressure and force a clean allocation cycle.",
            "critical",
            [
                annotate_pod(row.get("pod"), "observability.ai/memory-remediation", "required", row.get("namespace")),
                delete_pod(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if is_anomaly(row.get("anomaly"))
    ]


def restart_remediations(rows):
    return [
        remediation(
            "Restart Agent",
            row.get("pod"),
            "Repeated pod restarts detected",
            "Annotate and recreate the unstable pod so Kubernetes schedules a clean replacement.",
            "warning",
            [
                annotate_pod(row.get("pod"), "observability.ai/restart-remediation", "required", row.get("namespace")),
                delete_pod(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if float(row.get("restarts", 0)) > 0
    ]


def network_remediations(rows):
    return [
        remediation(
            "Network Agent",
            row.get("pod"),
            "Possible data leak or abnormal egress detected",
            "Quarantine the pod with labels and restart the workload to stop suspicious egress.",
            "critical",
            [
                label_pod(row.get("pod"), "observability.ai/quarantine", "true", row.get("namespace")),
                annotate_pod(row.get("pod"), "observability.ai/network-remediation", "egress-quarantine", row.get("namespace")),
                rollout_restart(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if is_anomaly(row.get("anomaly")) or transmit_heavy(row)
    ]


def filesystem_remediations(rows):
    return [
        remediation(
            "Filesystem Agent",
            row.get("pod"),
            "Filesystem pressure detected",
            "Mark the pod for storage cleanup and restart the workload if pressure remains high.",
            "warning",
            [
                annotate_pod(row.get("pod"), "observability.ai/storage-cleanup", "required", row.get("namespace")),
                rollout_restart(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if is_anomaly(row.get("anomaly")) or float(row.get("usage_percent", 0)) >= 65
    ]


def readiness_remediations(rows):
    return [
        remediation(
            "Readiness Agent",
            row.get("pod"),
            "Pod is not ready",
            "Recreate the pod so Kubernetes can rerun probes and attach a healthy replacement.",
            "critical",
            [
                annotate_pod(row.get("pod"), "observability.ai/readiness-remediation", "required", row.get("namespace")),
                delete_pod(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if float(row.get("ready", row.get("value", 0))) != 1
    ]


def phase_remediations(rows):
    return [
        remediation(
            "Phase Agent",
            row.get("pod"),
            f"Pod phase is {row.get('phase')}",
            "Recreate failed pods and mark pending pods for scheduling review.",
            "critical" if row.get("phase") == "Failed" else "warning",
            [
                annotate_pod(row.get("pod"), "observability.ai/phase-remediation", row.get("phase", "unknown"), row.get("namespace")),
                delete_pod(row.get("pod"), row.get("namespace"))
            ]
        )
        for row in rows
        if row.get("phase") in ["Pending", "Failed", "Unknown"]
    ]


def node_remediations(rows):
    return [
        remediation(
            "Node Agent",
            row.get("node"),
            f"Node condition {row.get('condition')} is active",
            "Cordon the unhealthy node to stop new scheduling while pressure is investigated.",
            "critical",
            [
                cordon_node(row.get("node")),
                annotate_node(row.get("node"), "observability.ai/node-remediation", row.get("condition", "pressure"))
            ]
        )
        for row in rows
        if row.get("severity") == "critical" and float(row.get("value", 0)) == 1
    ]


def remediation(agent, target, issue, resolution, severity, commands):
    return {
        "agent": agent,
        "target": target or "unknown",
        "issue": issue,
        "resolution": resolution,
        "severity": severity,
        "commands": [command for command in commands if "unknown" not in command["command"]]
    }


def build_action(index, issue):
    return {
        "id": f"rem-{index}",
        "agent": issue["agent"],
        "target": issue["target"],
        "issue": issue["issue"],
        "resolution": issue["resolution"],
        "severity": issue["severity"],
        "commands": issue["commands"]
    }


def build_timeline(status):
    if status == "resolved":
        states = ["complete", "complete", "complete", "complete"]
    elif status == "ready":
        states = ["complete", "complete", "ready", "ready"]
    else:
        states = ["complete", "complete", "failed", "blocked"]

    return [
        {"step": "Detected", "status": states[0]},
        {"step": "Planned", "status": states[1]},
        {"step": "Executing", "status": states[2]},
        {"step": "Verifying", "status": states[3]}
    ]


def action_status(results):
    if not results:
        return "blocked"

    if all(result["status"] == "complete" for result in results):
        return "resolved"

    if all(result["status"] in ["ready", "complete"] for result in results):
        return "ready"

    return "blocked"


def is_anomaly(value):
    return float(value or 0) in [-1, 1]


def transmit_heavy(row):
    receive_bps = float(row.get("receive_bps", 0))
    transmit_bps = float(row.get("transmit_bps", 0))
    return transmit_bps > 0 and transmit_bps > receive_bps * 2


def namespace(namespace):
    return namespace or DEFAULT_NAMESPACE


def resolve_workload(pod, pod_namespace=None):
    if not pod or pod == "unknown":
        return pod, "unknown"

    ns = namespace(pod_namespace)
    try:
        # Check if pod has an owner
        cmd = ["kubectl", "get", "pod", pod, "-n", ns, "-o", "jsonpath={.metadata.ownerReferences[0].name}|{.metadata.ownerReferences[0].kind}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('|')
            if len(parts) == 2:
                owner_name, owner_kind = parts
                if owner_kind == "ReplicaSet":
                    # Check if ReplicaSet has an owner (Deployment)
                    cmd_rs = ["kubectl", "get", "replicaset", owner_name, "-n", ns, "-o", "jsonpath={.metadata.ownerReferences[0].name}|{.metadata.ownerReferences[0].kind}"]
                    result_rs = subprocess.run(cmd_rs, capture_output=True, text=True, check=False)
                    if result_rs.returncode == 0 and result_rs.stdout.strip():
                        parts_rs = result_rs.stdout.strip().split('|')
                        if len(parts_rs) == 2:
                            parent_name, parent_kind = parts_rs
                            if parent_kind == "Deployment":
                                return parent_name, "deployment"
                elif owner_kind in ["Deployment", "StatefulSet", "DaemonSet"]:
                    return owner_name, owner_kind.lower()
    except Exception:
        pass

    return pod, "pod"


def annotate_pod(pod, key, value, pod_namespace=None):
    return {
        "label": f"Annotate pod {pod}",
        "command": ["kubectl", "annotate", "pod", pod or "unknown", f"{key}={value}", "--overwrite", "-n", namespace(pod_namespace)]
    }


def annotate_node(node, key, value):
    return {
        "label": f"Annotate node {node}",
        "command": ["kubectl", "annotate", "node", node or "unknown", f"{key}={value}", "--overwrite"]
    }


def label_pod(pod, key, value, pod_namespace=None):
    return {
        "label": f"Label pod {pod}",
        "command": ["kubectl", "label", "pod", pod or "unknown", f"{key}={value}", "--overwrite", "-n", namespace(pod_namespace)]
    }


def rollout_restart(pod, pod_namespace=None):
    workload_name, workload_kind = resolve_workload(pod, pod_namespace)

    if workload_kind == "deployment":
        return {
            "label": f"Restart workload {workload_name}",
            "command": ["kubectl", "rollout", "restart", f"deployment/{workload_name}", "-n", namespace(pod_namespace)]
        }

    return delete_pod(pod, pod_namespace)


def delete_pod(pod, pod_namespace=None):
    return {
        "label": f"Recreate pod {pod}",
        "command": ["kubectl", "delete", "pod", pod or "unknown", "-n", namespace(pod_namespace)]
    }


def cordon_node(node):
    return {
        "label": f"Cordon node {node}",
        "command": ["kubectl", "cordon", node or "unknown"]
    }

