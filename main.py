
from modules.v1438_core.brain import unified_brain

def run(symbol_data):
    return unified_brain(symbol_data)

if __name__ == "__main__":
    print(run({"price":100,"volume":2,"rsi":30,"sentiment":1}))
