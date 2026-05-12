def generate_cpu_insight(pod, value, anomaly):

    if anomaly == -1:

        return f"Pod {pod} is showing abnormal CPU usage with value {value:.4f}"

    return f"Pod {pod} is operating normally"
