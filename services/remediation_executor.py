import os
import shlex
import subprocess


AUTO_REMEDIATE = os.getenv("AI_OBSERVABILITY_AUTO_REMEDIATE", "false").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("AI_OBSERVABILITY_REMEDIATION_TIMEOUT", "60"))

ALLOWED_COMMAND_PREFIXES = [
    ["kubectl", "annotate"],
    ["kubectl", "label"],
    ["kubectl", "rollout", "restart"],
    ["kubectl", "delete", "pod"],
    ["kubectl", "cordon"],
    ["kubectl", "uncordon"]
]


def execute_remediation_commands(commands):
    results = []

    for command in commands:
        if not AUTO_REMEDIATE:
            results.append(command_result(command, "ready", "Automatic execution is disabled."))
            continue

        results.append(run_remediation_command(command))

    return results


def is_allowed(command):
    return any(command[:len(prefix)] == prefix for prefix in ALLOWED_COMMAND_PREFIXES)


def run_remediation_command(command):
    command_parts = command["command"]

    if isinstance(command_parts, str):
        command_parts = shlex.split(command_parts)

    normalized_command = {**command, "command": command_parts}

    if not is_allowed(command_parts):
        return command_result(normalized_command, "blocked", "Command is outside the remediation allowlist.")

    try:
        completed = subprocess.run(
            command_parts,
            capture_output=True,
            check=False,
            text=True,
            timeout=DEFAULT_TIMEOUT
        )

        status = "complete" if completed.returncode == 0 else "failed"
        output = completed.stdout.strip() or completed.stderr.strip() or f"Return code {completed.returncode}"
        return command_result(normalized_command, status, output)
    except subprocess.TimeoutExpired:
        return command_result(normalized_command, "failed", "Command timed out.")
    except OSError as error:
        return command_result(normalized_command, "failed", str(error))


def command_result(command, status, output):
    return {
        "label": command["label"],
        "command": " ".join(command["command"]),
        "status": status,
        "output": output
    }
