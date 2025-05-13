# performance.py
import math

class PerformanceMonitor:
    """
    PerformanceMonitor collects network performance metrics:
      - Packet Delivery Ratio (PDR)
      - Average End-to-End Delay
      - Control Overhead (number of control packets sent)
      - Energy consumption (approx TX/RX cost)
      - Throughput (bits per second)
    """
    def __init__(self):
        self.total_data_sent = 0
        self.total_data_delivered = 0
        self.sum_end_to_end_delays = 0.0
        self.data_packet_info = {}  # packet_id -> (creation_time, packet_size)
        self.control_packets_sent = 0
        self.data_packets_sent = 0
        self.TX_COST = 0.75
        self.RX_COST = 0.25
        self.energy_used = 0.0
        self.earliest_data_send_time = math.inf
        self.latest_data_delivery_time = 0.0
        self.total_bytes_delivered = 0

    def on_data_packet_created(self, packet_id, creation_time, packet_size=64):
        self.total_data_sent += 1
        self.data_packets_sent += 1
        self.earliest_data_send_time = min(self.earliest_data_send_time, creation_time)
        self.data_packet_info[packet_id] = (creation_time, packet_size)

    def on_data_packet_delivered(self, packet_id, delivery_time):
        self.total_data_delivered += 1
        if packet_id in self.data_packet_info:
            creation_time, packet_size = self.data_packet_info[packet_id]
            delay = delivery_time - creation_time
            self.sum_end_to_end_delays += delay
            self.latest_data_delivery_time = max(self.latest_data_delivery_time, delivery_time)
            self.total_bytes_delivered += packet_size

    def on_control_packet_sent(self):
        self.control_packets_sent += 1

    def on_transmit(self):
        self.energy_used += self.TX_COST

    def on_receive(self):
        self.energy_used += self.RX_COST

    def get_pdr(self):
        if self.total_data_sent == 0:
            return 0.0
        return self.total_data_delivered / float(self.total_data_sent)

    def get_average_delay(self):
        if self.total_data_delivered == 0:
            return 0.0
        return self.sum_end_to_end_delays / float(self.total_data_delivered)

    def get_overhead_packets(self):
        return self.control_packets_sent

    def get_energy_used(self):
        return self.energy_used

    def get_throughput(self):
        if self.latest_data_delivery_time <= self.earliest_data_send_time:
            return 0.0
        total_seconds = self.latest_data_delivery_time - self.earliest_data_send_time
        total_bits = self.total_bytes_delivered * 8
        return total_bits / total_seconds

    def print_final_results(self):
        print("---- Performance Metrics ----")
        print(f"Total data sent: {self.total_data_sent}")
        print(f"Total data delivered: {self.total_data_delivered}")
        print(f"Packet Delivery Ratio (PDR): {self.get_pdr():.2f}")
        print(f"Average End-to-End Delay: {self.get_average_delay():.4f} s")
        print(f"Control Packets Sent: {self.control_packets_sent}")
        print(f"Energy Used (approx): {self.get_energy_used():.2f} units")
        print(f"Throughput: {self.get_throughput():.2f} bits/s")
        print("--------------------------------")
