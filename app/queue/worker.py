
import time
import threading
from app.queue.queue import QUEUE

def worker():
    while True:
        try:
            if QUEUE:
                task = QUEUE.popleft()
                task()
        except Exception as e:
            print("worker error:", e)

        time.sleep(0.5)

def start_worker():
    t = threading.Thread(target=worker, daemon=True)
    t.start()
