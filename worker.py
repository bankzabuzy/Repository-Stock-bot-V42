
import time

def run_worker():
    while True:
        print("[V1438.6 WORKER] alive tick")
        time.sleep(30)

if __name__ == "__main__":
    run_worker()
