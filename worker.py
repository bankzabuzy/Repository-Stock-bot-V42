
# SAFE WORKER ENTRY (prevents crash loop)
import time

def start_worker():
    while True:
        # placeholder safe loop (no crash)
        time.sleep(60)

if __name__ == "__main__":
    start_worker()
