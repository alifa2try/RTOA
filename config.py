# config.py
import os
import builtins

def log(*args, **kwargs):
    """
    Log messages to both stdout and to output.txt.
    """
    with open('output.txt', 'a') as f:
        builtins.print(*args, **kwargs, file=f)
    builtins.print(*args, **kwargs)

def configure_simulation():
    """
    Returns a dictionary of fixed simulation parameters.
    Old output files are removed.
    """
    for filename in ['output.txt', 'output.png']:
        if os.path.exists(filename):
            os.remove(filename)

    print("Using final tuned simulation parameters (no prompt).")
    config = {
        "RANDOM_SEED": 9999,

        # Node count
        "NUM_NODES": 100,

        # Spread out the nodes to reduce density
        "AREA_WIDTH": 140,
        "AREA_HEIGHT": 140,

        # Minimum spacing so nodes don't cluster
        "MINIMUM_DISTANCE": 6,

        # Connection range – lower neighbor count to reduce overhead
        "CONNECTION_RANGE": 100,

        # Large DIO interval to avoid frequent control floods
        "DIO_INTERVAL": 200,

        # Node creation delay
        "NODE_CREATION_INTERVAL": 1,

        # Extended runtime to allow routes to stabilize
        "RUNTIME": 5000,

        # Slower data rate, reduce collisions
        "TRAFFIC_INTERVAL": 15,

        # Attack config
        "ENABLE_ATTACK": False,
        "MALICIOUS_PERCENTAGE": 0.00
    }
    return config
