# run_simulation.py
import random
import matplotlib.pyplot as plt
from config import configure_simulation, log
from environment import setup_environment
from node import Packet
from malicious import RoutingTableOverloadAttack
from performance import PerformanceMonitor

def main():
    config = configure_simulation()
    random.seed(config["RANDOM_SEED"])

    perf_monitor = PerformanceMonitor()
    env, nodes = setup_environment(config, performance_monitor=perf_monitor)

    # Let node creation finish
    creation_time = config["NUM_NODES"] * config["NODE_CREATION_INTERVAL"]
    buffer_time = 1
    env.run(until=creation_time + buffer_time)

    if config.get("ENABLE_ATTACK", False):
        total_nodes = config["NUM_NODES"]
        malicious_percentage = config.get("MALICIOUS_PERCENTAGE", 0.0)
        num_malicious = int(total_nodes * malicious_percentage)

        if num_malicious > 0:
            possible_indices = range(1, total_nodes)
            chosen_attackers = random.sample(possible_indices, k=num_malicious)
            print(f">> Selecting {num_malicious} malicious node(s) out of {total_nodes} total.")
            for attacker_idx in chosen_attackers:
                attacker_node = nodes[attacker_idx]
                print(f"   - Setting attacker as {attacker_node.node_id}")
                attack = RoutingTableOverloadAttack(env, attacker_node, config)
                env.process(attack.launch())
        else:
            print(">> MALICIOUS_PERCENTAGE is 0 or results in zero attackers.")
    else:
        print(">> Malicious node is turned off.")

    # Start normal traffic AFTER warm-up
    WARMUP_TIME = 120  # big warm-up
    env.process(generate_traffic(env, nodes, config["TRAFFIC_INTERVAL"], perf_monitor, start_delay=WARMUP_TIME))

    # Run remainder
    remaining = config["RUNTIME"] - (creation_time + buffer_time)
    if remaining < 0:
        remaining = 0
    env.run(until=env.now + remaining)

    print("SimPy simulation ended!")
    plot_topology(nodes, config)
    log("Simulation complete.")
    perf_monitor.print_final_results()

def generate_traffic(env, nodes, interval, perf_monitor, start_delay=0):
    """
    Wait 'start_delay' for warm-up, then create data packets every 'interval' seconds.
    """
    yield env.timeout(start_delay)
    packet_id = 0
    while True:
        yield env.timeout(interval)
        if len(nodes) < 2:
            continue
        src = random.choice(nodes)
        dst = random.choice(nodes)
        if src == dst:
            continue
        pkt = Packet(src.node_id, dst.prefix)
        pkt.packet_id = f"pkt_{packet_id}"
        packet_id += 1
        if perf_monitor:
            perf_monitor.on_data_packet_created(pkt.packet_id, env.now)
        src.send_packet(pkt, src)
        log(f"{env.now:.2f} TRAFFIC: {src.node_id} -> {dst.prefix}")

def plot_topology(nodes, config):
    plt.figure(figsize=(6,6))
    plt.title("RPL Storing-Mode with Attack (Node00 = Root)")
    plt.xlabel("Width (m)")
    plt.ylabel("Height (m)")
    drawn_edges = set()
    for node in nodes:
        plt.scatter(node.position[0], node.position[1], color=node.color, label=node.node_id)
        label_txt = node.prefix.replace("2001:db8::", "::")
        plt.text(node.position[0], node.position[1],
                 f"{node.node_id}\n{label_txt}",
                 fontsize=6, ha='center', va='bottom', color=node.color)
        for nbr in node.neighbors:
            edge = tuple(sorted([node.node_id, nbr.node_id]))
            if edge not in drawn_edges:
                drawn_edges.add(edge)
                plt.plot([node.position[0], nbr.position[0]],
                         [node.position[1], nbr.position[1]],
                         color='blue', alpha=0.5, linestyle='dotted', linewidth=0.7)
        for lost in node.lost_neighbors:
            edge = tuple(sorted([node.node_id, lost.node_id]))
            if edge not in drawn_edges:
                drawn_edges.add(edge)
                plt.plot([node.position[0], lost.position[0]],
                         [node.position[1], lost.position[1]],
                         color='red', alpha=0.3, linewidth=0.7)
    plt.xlim(0, config["AREA_WIDTH"])
    plt.ylim(0, config["AREA_HEIGHT"])
    plt.gca().set_aspect('equal', 'box')
    plt.grid(False)
    plt.savefig("output.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    main()
