import os
import sys
import time
import traceback

LOG_PATH = "/root/vision_runtime.log"


def log(message):
    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        file.flush()
        os.fsync(file.fileno())


def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] " "UNCAUGHT EXCEPTION\n")
        traceback.print_exception(
            exc_type,
            exc_value,
            exc_traceback,
            file=file,
        )
        file.flush()
        os.fsync(file.fileno())

    # Preserve normal error output and Maix's last_run.log.
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
