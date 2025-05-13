# malicious.py
print(f"Malicious code loaded from: {__file__}")

import random
from config import log

class RoutingTableOverloadAttack:
    """
    A malicious attack that spams parent nodes (nodes with at least one
    entry in downward_routes) with fake DAO messages.
    """
    def __init__(self, env, attacker_node, config):
        self.env = env
        self.attacker_node = attacker_node
        self.config = config
        self.attack_interval = 2
        self.max_spoofs = 50

    def launch(self):
        print(f">> Attacker {self.attacker_node.node_id} launch() called at t={self.env.now} <<")
        yield self.env.timeout(1)
        count = 0
        while count < self.max_spoofs:
            log(f"{self.env.now:.2f} [ATTACK-DEBUG] {self.attacker_node.node_id} checking for parents (count={count})...")
            yield self.env.timeout(self.attack_interval)
            possible_victims = [
                node for node in self.attacker_node.all_nodes
                if node != self.attacker_node and len(node.downward_routes) > 0
            ]
            log(f"{self.env.now:.2f} [ATTACK-DEBUG] found {len(possible_victims)} potential victims with children.")
            if not possible_victims:
                log(f"{self.env.now:.2f} [ATTACK] {self.attacker_node.node_id} found no valid 'parents' to attack.")
                continue
            victim_node = random.choice(possible_victims)
            fake_num = random.randint(1000, 9999)
            fake_prefix = f"2001:db8::{fake_num:x}"
            log(f"{self.env.now:.2f} [ATTACK] {self.attacker_node.node_id} -> {victim_node.node_id}, prefix={fake_prefix}")
            yield self.env.process(victim_node.receive_dao(fake_prefix, self.attacker_node))
            count += 1
        log(f"{self.env.now:.2f} [ATTACK] {self.attacker_node.node_id} finished sending {self.max_spoofs} spoofs.")
