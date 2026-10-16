def analyze_plot(length, width, front, rear, left, right):
    """All lengths in feet. Returns results, or None if setbacks are too large."""
    plot_area = length * width
    buildable_length = length - front - rear
    buildable_width = width - left - right

    if buildable_length <= 0 or buildable_width <= 0:
        return None

    buildable_area = buildable_length * buildable_width
    utilization = buildable_area / plot_area * 100

    return {
        "plot_area": plot_area,
        "buildable_length": buildable_length,
        "buildable_width": buildable_width,
        "buildable_area": buildable_area,
        "utilization": utilization,
        "setback_area": plot_area - buildable_area,
    }