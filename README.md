# BridgeGuard: Energy-Aware TinyML for Structural Health Monitoring

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Machine Learning](https://img.shields.io/badge/TinyML-Random_Forest-orange.svg)
![Architecture](https://img.shields.io/badge/Architecture-Edge%E2%86%92Fog%E2%86%92Cloud-success.svg)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)

BridgeGuard is a decentralized, cyber-physical Structural Health Monitoring (SHM) system. It utilizes Edge-Autonomous TinyML, Fast Fourier Transform (FFT) spectral engineering, and a Two-Stage Cascade logic to detect micro-fractures in bridge infrastructure with sub-millisecond latency while significantly reducing sensor power consumption.

---

## Table of Contents
1. [System Objective](#system-objective)
2. [Key Architecture & Features](#key-architecture--features)
3. [TinyML Performance Benchmarks](#tinyml-performance-benchmarks)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Running the Live Demo](#running-the-live-demo)

---

## System Objective
Traditional SHM systems face an energy-bandwidth trade-off. Streaming high-fidelity sensor data to a centralized cloud server drains IoT battery life rapidly and introduces network latency during critical structural events.

BridgeGuard addresses this by shifting inference to the Edge. By processing vibration data locally, the system achieves hard real-time actuation (such as triggering traffic barriers) while only transmitting sparse, asynchronous telemetry to the Fog and Cloud layers.

---

## Key Architecture & Features

The system is built on a decoupled, three-tier architecture:

### 1. The Intelligent Edge (Microcontroller Node)
* **Edge-Level Data Imputation:** A Zero-Order Hold (ZOH) engine automatically handles dropped packets and `NaN` values on the fly to prevent pipeline crashes.
* **Two-Stage Cascade AI:**
  * *Stage 1 (Variance Gate):* A lightweight O(1) heuristic monitors structural variance. If variance is < 0.001, the primary ML model remains in sleep mode.
  * *Stage 2 (Inference):* Wakes the Random Forest model only when an anomaly is detected.
* **Adaptive Sampling Rate (ASR):** The system dynamically adjusts hardware polling from 10Hz (idle state) up to 100Hz to capture high-resolution data during an event.
* **FFT Spectral Engineering:** Converts raw time-domain vibrations into the frequency domain to detect natural resonance shifts indicative of structural damage.

### 2. The Fog Gateway (Regional Telemetry)
* **Asynchronous UDP Server:** Listens on `Port 5005` for lightweight heartbeat pings and hazard alerts from local Edge Nodes.
* **Regional Aggregation:** Filters out false positives and triggers a master lockdown protocol if multiple consecutive alerts are received.

### 3. The Cloud Layer (Global Historian)
* **Batch Synchronization:** The Fog Node batches aggregated data and pushes it to cloud storage.
* **Degradation Analytics:** Generates time-series visualizations to track structural health over extended periods for predictive maintenance scheduling.

---

## TinyML Performance Benchmarks

The core inference engine is an optimized Random Forest Ensemble (100 Trees, Depth 10) trained on multi-axial vibration and strain data.

| Metric | Score / Value | Engineering Significance |
| :--- | :--- | :--- |
| **Accuracy** | `98.2%` | Reliable state classification across baseline and damage states. |
| **Recall**| `97.2%` | Minimizes false negatives for critical safety events. |
| **Model Size** | `~1.4 MB` | Compatible with the Flash memory constraints of ESP32/STM32 microcontrollers. |
| **Inference Time** | `4.11 ms` | Meets the < 50ms deadline required for hard real-time safety actuation. |
| **Latency Jitter** | `0.92 ms` | Demonstrates deterministic execution suitable for cyber-physical systems. |

---

## Project Structure

```text
BridgeGuard-SHM/
│
├── data/
│   └── raw/
│       └── sensor_data.csv          # Simulated physical sensor dataset
│
├── edge_node/
│   ├── edge_inference.py            # Main Edge script (Cascade logic, ASR, UDP Tx)
│   ├── edge_shm_model.pkl           # Serialized Random Forest model
│   └── model_features.pkl           # 14-dimensional feature vector names
│
├── fog_node/
│   └── fog_aggregator.py            # UDP Server, Heartbeat monitor, Alert logic
│
├── cloud_layer/
│   ├── cloud_analytics.py           # Dashboard generator (Matplotlib)
│   ├── aggregated_bridge_health.csv # Synced Fog data (Generated at runtime)
│   └── bridge_health_report.png     # Output degradation graph
│
├── notebooks/
│   └── 01_model_training.ipynb      # ML Pipeline (Data prep, FFT, Training, Eval)
│
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/BridgeGuard-SHM.git](https://github.com/your-username/BridgeGuard-SHM.git)
   cd BridgeGuard-SHM
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Requires: pandas, numpy, scikit-learn, joblib, matplotlib)*

---

## Running the Live Demo

To simulate the cyber-physical feedback loop, run the Fog Node and Edge Node concurrently in two separate terminal windows.

**Terminal 1: Start the Fog Gateway**
```bash
python fog_node/fog_aggregator.py
```
*Expected Output:* The Fog node initializes and listens on UDP `127.0.0.1:5005`.

**Terminal 2: Start the Edge Node (Sensor Stream)**
```bash
python edge_node/edge_inference.py
```
*Expected Behavior:*
1. The Edge node boots in a 10Hz low-power mode, transmitting periodic heartbeats.
2. A simulated structural event is injected via the dataset.
3. The Edge node dynamically throttles to 100Hz, detects the anomaly, triggers local actuation, and transmits a UDP alert.
4. The Fog node receives the alert, aggregates the data, and synchronizes the batch to `cloud_layer/aggregated_bridge_health.csv`.