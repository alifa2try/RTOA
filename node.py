# node.py
import random
from config import log

class Packet:
    """
    A simple data packet carrying destination prefix and source node ID.
    A unique packet_id is assigned for performance monitoring.
    """
    _id_counter = 0

    def __init__(self, src_id, dst_prefix, packet_size=64):
        self.src_id = src_id
        self.dst_prefix = dst_prefix
        self.packet_size = packet_size
        self.packet_id = Packet._id_counter
        Packet._id_counter += 1

    def __repr__(self):
        return f"<Packet id={self.packet_id} src={self.src_id} dst={self.dst_prefix}>"

class Node:
    """
    An RPL node in storing mode with a large 'max_downward_routes'
    to avoid 'OVERLOADED' rejections.
    """

    def __init__(self, env, node_id, position, all_nodes, config, is_root=False, performance_monitor=None):
        self.env = env
        self.node_id = node_id
        self.position = position
        self.all_nodes = all_nodes
        self.config = config
        self.is_root = is_root
        self.performance_monitor = performance_monitor

        self.parent = None
        self.neighbors = []
        self.lost_neighbors = []
        self.downward_routes = {}

        # Enough to store big sub-DODAGs
        self.max_downward_routes = 800  

        if self.is_root:
            self.prefix = "2001:db8::1"
        else:
            node_num_hex = int(node_id[4:])
            self.prefix = f"2001:db8::{node_num_hex:02x}"

        self.Imin = 1
        self.Imax = 8
        self.I = self.Imin
        self.t = random.uniform(self.Imin, self.I)

        self.color = (random.random(), random.random(), random.random())
        self.inbox = []
        self.env.process(self.run_inbox())

    def calculate_distance(self, other_pos):
        return ((self.position[0] - other_pos[0])**2
                + (self.position[1] - other_pos[1])**2)**0.5

    def run_inbox(self):
        while True:
            if self.inbox:
                item = self.inbox.pop(0)
                yield self.env.timeout(0.2)
                if isinstance(item, tuple):
                    msg_type = item[0]
                    if msg_type == "DAO-ACK":
                        _, from_node, child_prefix, status = item
                        self.receive_dao_ack(from_node, child_prefix, status)
                    elif msg_type == "DIS":
                        _, sender = item
                        self.env.process(self.receive_dis(sender))
                    elif msg_type == "DIO":
                        _, sender = item
                        self.env.process(self.receive_dio(sender))
                    elif msg_type == "DAO":
                        _, child_node, child_prefix = item
                        self.env.process(self.receive_dao(child_prefix, child_node))
                else:
                    # Data packet
                    pkt = item
                    if self.performance_monitor:
                        self.performance_monitor.on_receive()
                    self.handle_packet(pkt)
            else:
                yield self.env.timeout(0.1)

    def handle_packet(self, packet):
        dst_prefix = packet.dst_prefix
        if dst_prefix == self.prefix:
            log(f"{self.env.now:.2f} {self.node_id} DELIVERS {packet}")
            if self.performance_monitor:
                self.performance_monitor.on_data_packet_delivered(packet.packet_id, self.env.now)
            return

        if dst_prefix in self.downward_routes:
            child = self.downward_routes[dst_prefix]
            log(f"{self.env.now:.2f} {self.node_id} FORWARDS DOWN {packet} to {child.node_id}")
            self.send_packet(packet, child)
            return

        if self.parent:
            log(f"{self.env.now:.2f} {self.node_id} FORWARDS UP {packet} to {self.parent.node_id}")
            self.send_packet(packet, self.parent)
        else:
            log(f"{self.env.now:.2f} {self.node_id} DROP (no route) {packet}")

    def send_packet(self, packet, next_hop):
        if self.performance_monitor:
            self.performance_monitor.on_transmit()

        def _delay_tx(env):
            yield env.timeout(0.1)
            next_hop.inbox.append(packet)

        self.env.process(_delay_tx(self.env))

    # DAO-ACK and Control Packets
    def send_dao_ack(self, child_node, child_prefix, status=0):
        log(f"{self.env.now:.2f} {self.node_id} sends DAO-ACK (status={status}) to {child_node.node_id} for {child_prefix}")
        if self.performance_monitor:
            self.performance_monitor.on_control_packet_sent()
            self.performance_monitor.on_transmit()

        def _delay_ack(env):
            yield env.timeout(0.1)
            child_node.inbox.append(("DAO-ACK", self, child_prefix, status))

        self.env.process(_delay_ack(self.env))

    def receive_dao_ack(self, from_node, child_prefix, status):
        if status == 0:
            log(f"{self.env.now:.2f} {self.node_id} received DAO-ACK from {from_node.node_id}; prefix={child_prefix}, status=SUCCESS")
        else:
            log(f"{self.env.now:.2f} {self.node_id} received DAO-ACK from {from_node.node_id}; prefix={child_prefix}, status=ERROR-{status}")

            
    def discover_neighbors(self):
        yield self.env.timeout(0.1)
        if self.performance_monitor:
            self.performance_monitor.on_control_packet_sent()
            self.performance_monitor.on_transmit()

        for node in self.all_nodes:
            if node != self and self.calculate_distance(node.position) <= self.config["CONNECTION_RANGE"]:
                node.inbox.append(("DIS", self))
                log(f"{self.env.now:.2f} {self.node_id} sends DIS to {node.node_id}")
        yield self.env.timeout(0)

    def receive_dis(self, sender):
        dist = self.calculate_distance(sender.position)
        if sender not in self.neighbors and dist <= self.config["CONNECTION_RANGE"]:
            self.neighbors.append(sender)
            if self not in sender.neighbors:
                sender.neighbors.append(self)
            if self.performance_monitor:
                self.performance_monitor.on_control_packet_sent()
                self.performance_monitor.on_transmit()
            sender.inbox.append(("DIO", self))
            log(f"{self.env.now:.2f} {self.node_id} received DIS from {sender.node_id}; new neighbor: {sender.node_id}")
        yield self.env.timeout(0.1)

    def send_dio(self):
        while True:
            for nbr in self.neighbors:
                if nbr.parent != self:
                    if self.performance_monitor:
                        self.performance_monitor.on_control_packet_sent()
                        self.performance_monitor.on_transmit()
                    nbr.inbox.append(("DIO", self))
                    log(f"{self.env.now:.2f} {self.node_id} sends DIO to {nbr.node_id}")
            yield self.env.timeout(self.config["DIO_INTERVAL"])

    def receive_dio(self, sender):
        if self.is_root:
            return
        if not self.parent:
            self.parent = sender
            self.prefix = f"{sender.prefix}:{int(self.node_id[4:]):02x}"
            yield self.env.process(self.send_dao())
            log(f"{self.env.now:.2f} {self.node_id} got new parent {sender.node_id}; prefix={self.prefix}")
        else:
            dist_sender = self.calculate_distance(sender.position)
            dist_curr = self.calculate_distance(self.parent.position)
            if dist_sender < dist_curr and sender.parent != self:
                self.parent = sender
                self.prefix = f"{sender.prefix}:{int(self.node_id[4:]):02x}"
                yield self.env.process(self.send_dao())
                log(f"{self.env.now:.2f} {self.node_id} switched parent to {sender.node_id}; prefix={self.prefix}")
        yield self.env.timeout(0)

    def send_dao(self):
        log(f"{self.env.now:.2f} {self.node_id} sends DAO up to {self.parent.node_id} for prefix={self.prefix}")
        if self.performance_monitor:
            self.performance_monitor.on_control_packet_sent()
            self.performance_monitor.on_transmit()
        self.parent.inbox.append(("DAO", self, self.prefix))
        yield self.env.timeout(0)

    def receive_dao(self, child_prefix, child_node):
        if (child_prefix in self.downward_routes
                and self.downward_routes[child_prefix] == child_node):
            log(f"{self.env.now:.2f} {self.node_id} already has route {child_prefix} -> {child_node.node_id}, ignoring DAO.")
            yield self.env.timeout(0)
            return
        if len(self.downward_routes) >= self.max_downward_routes:
            log(f"{self.env.now:.2f} {self.node_id} is OVERLOADED, ignoring DAO for {child_prefix} from {child_node.node_id}")
            yield self.env.timeout(0)
            return

        self.downward_routes[child_prefix] = child_node
        log(f"{self.env.now:.2f} {self.node_id} stores downward route: {child_prefix} -> {child_node.node_id}")
        if self.parent:
            log(f"{self.env.now:.2f} {self.node_id} forwards DAO to parent {self.parent.node_id} for {child_prefix}")
            if self.performance_monitor:
                self.performance_monitor.on_control_packet_sent()
                self.performance_monitor.on_transmit()
            self.parent.inbox.append(("DAO", child_node, child_prefix))
        if hasattr(self, "send_dao_ack"):
            self.send_dao_ack(child_node, child_prefix, status=0)
        yield self.env.timeout(0)

    def send_dis(self):
        """
        Called by trickle_timer() if node has no neighbors.
        We broadcast DIS to see if any node is within range.
        """
        for n in self.all_nodes:
            if n != self and self.calculate_distance(n.position) <= self.config["CONNECTION_RANGE"]:
                if self.performance_monitor:
                    self.performance_monitor.on_control_packet_sent()
                    self.performance_monitor.on_transmit()
                n.inbox.append(("DIS", self))
                log(f"{self.env.now:.2f} {self.node_id} sends DIS to {n.node_id}")
        yield self.env.timeout(0.1)

    def reset_trickle(self):
        self.I = self.Imin
        self.t = random.uniform(self.Imin, self.I)

    def trickle_timer(self):
        while True:
            yield self.env.timeout(self.t)
            if not self.neighbors:
                yield self.env.process(self.send_dis())
                log(f"{self.env.now:.2f} {self.node_id} sends DIS broadcast (Trickle)")
            self.I = min(self.I * 2, self.Imax)
            self.t = random.uniform(self.Imin, self.I)

    def network_disruption(self):
        while True:
            yield self.env.timeout(self.t)
            if False:
                log(f"{self.env.now:.2f} {self.node_id} network disruption triggered!")
                self.lost_neighbors.clear()
                for neighbor in self.neighbors:
                    if self in neighbor.neighbors:
                        neighbor.neighbors.remove(self)
                for neighbor in self.neighbors:
                    self.lost_neighbors.append(neighbor)
                self.neighbors.clear()
                yield self.env.process(self.discover_neighbors())
