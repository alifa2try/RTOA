import numpy as np
import matplotlib.pyplot as plt

# Define the metrics for each scenario (from your 50-node results as an example)
# Metrics: PDR, (inverted) AE2ED, (inverted) Overhead, (inverted) Energy, Throughput
# For metrics where lower is better, we use the reciprocal (or an appropriate transformation) to align with "higher is better".

# Reference values for 50 nodes (as baseline):
ref_pdr = 0.51
ref_delay = 7.0351        # Lower is better → use inverse: 1/7.0351
ref_overhead = 359891     # Lower is better → use inverse
ref_energy = 1111332.25   # Lower is better → use inverse
ref_throughput = 50.94

# Data for each scenario:
data = {
    "reference": [0.51, 1/7.0351, 1/359891, 1/1111332.25, 50.94],
    "10% malicious": [0.47, 1/6.9112, 1/361662, 1/1112678.25, 47.55],
    "20% malicious": [0.47, 1/7.6557, 1/363035, 1/1111943.25, 47.35],
    "30% malicious": [0.49, 1/7.0282, 1/364457, 1/1112089.75, 49.18],
}

# Normalize each metric relative to the reference scenario so that the reference becomes 1 for every metric.
labels = ['pdr', 'delay', 'overhead', 'energy', 'throughput']
ref_vals = np.array(data["reference"])

def normalize(scenario_vals):
    return np.array(scenario_vals) / ref_vals

# Normalize data for each scenario
normalized_data = {key: normalize(vals) for key, vals in data.items()}

# Radar chart settings
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]  # complete the loop

def plot_radar(data_dict, labels, angles):
    fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
    
    for scenario, values in data_dict.items():
        # Append first value to close the loop
        vals = values.tolist()
        vals += vals[:1]
        ax.plot(angles, vals, label=scenario)
        ax.fill(angles, vals, alpha=0.1)
    
    # Set the labels for each axis
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    
    # Set y-labels and limits: since all are normalized, 1 is baseline
    ax.set_yticks([0.5, 1.0, 1.5, 2.0])
    ax.set_yticklabels(["0.5", "1.0", "1.5", "2.0"])
    ax.set_ylim(0, max(2.0, np.max([np.max(vals) for vals in normalized_data.values()])))
    
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    plt.title("Normalized Performance Metrics Comparison")
    plt.tight_layout()
    plt.show()

plot_radar(normalized_data, labels, angles)
