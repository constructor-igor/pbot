def bytes_to_mb(bytes_value):
    mb_value = bytes_value / (1024 * 1024)
    return f"{mb_value:.3f} MB"