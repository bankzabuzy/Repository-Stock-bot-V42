
import time

# IMPORTANT:
# This worker is designed to be run as a SEPARATE PROCESS

def job_loop():
    while True:
        print("V1438.5 worker alive - processing tick")
        time.sleep(60)

if __name__ == "__main__":
    job_loop()
