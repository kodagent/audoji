import time


def seconds_to_minutes(seconds):
    return time.strftime("%M:%S", time.gmtime(seconds))


def minutes_to_seconds(minutes_str):
    struct_time = time.strptime(minutes_str, "%M:%S")
    total_seconds = struct_time.tm_min * 60 + struct_time.tm_sec
    return total_seconds
