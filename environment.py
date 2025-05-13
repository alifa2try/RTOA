# environment.py
import simpy
import random
from config import log
from node import Node

def setup_environment(config, performance_monitor=None):
    env = simpy.Environment()
    nodes = []

    def create_nodes():
        """
        Creates NUM_NODES in the environment, spaced so that
        no two nodes are within MINIMUM_DISTANCE.
        """
        for i in range(config["NUM_NODES"]):
            position = (
                round(random.uniform(0, config["AREA_WIDTH"]), 4),
                round(random.uniform(0, config["AREA_HEIGHT"]), 4)
            )

            valid_pos = False
            while not valid_pos:
                valid_pos = True
                for n in nodes:
                    if n.calculate_distance(position) < config["MINIMUM_DISTANCE"]:
                        valid_pos = False
                        position = (
                            round(random.uniform(0, config["AREA_WIDTH"]), 4),
                            round(random.uniform(0, config["AREA_HEIGHT"]), 4)
                        )
                        break

            is_root = (i == 0)
            node = Node(
                env=env,
                node_id=f"Node{i:02d}",
                position=position,
                all_nodes=nodes,
                config=config,
                is_root=is_root,
                performance_monitor=performance_monitor
            )
            nodes.append(node)

            # RPL processes
            env.process(node.discover_neighbors())
            env.process(node.send_dio())
            env.process(node.trickle_timer())
            env.process(node.network_disruption())

            log(f"{env.now:.2f} {node.node_id} created at {position}, is_root={is_root}")
            yield env.timeout(config["NODE_CREATION_INTERVAL"])

    env.process(create_nodes())
    return env, nodes
