
#!/bin/bash

# SAFE LAUNCH STRATEGY
# Web service
uvicorn app:app --host 0.0.0.0 --port $PORT
