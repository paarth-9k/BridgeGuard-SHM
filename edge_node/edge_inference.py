import pandas as pd
import numpy as np
import joblib
import time
import json
import logging
import socket
from collections import deque
import os

# ---------------------------------------------------------
# 1. Edge Node Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [EDGE NODE] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 2. Real-Time Edge Processing Class
# ---------------------------------------------------------
class BridgeEdgeNode:
    def __init__(self, model_path: str, features_path: str, window_size: int = 5):
        logger.info("Booting up Edge Node Interface (Energy-Aware Cascade Mode)...")
        
        self.model = joblib.load(model_path)
        self.feature_names = joblib.load(features_path)
        self.window_size = window_size
        self.data_buffer = deque(maxlen=window_size)
        
        self.is_awake = False
        self.awake_cooldown = 0  
        
        logger.info(f"Model loaded. Ready to monitor {len(self.feature_names)} features.")

    def _preprocess_tick(self, raw_dict: dict) -> dict:
        """
        EDGE-LEVEL DATA IMPUTATION:
        Cleans corrupt packets and handles missing sensor data on the fly.
        """
        cleaned = {}
        for key, val in raw_dict.items():
            # If the sensor dropped the packet (NaN or None)
            if pd.isna(val) or val is None or val == '':
                # Zero-Order Hold: Reuse the last known good value from the buffer
                if len(self.data_buffer) > 0:
                    cleaned[key] = self.data_buffer[-1].get(key, 0.0)
                    # We log it softly so we know the cleaning engine is working
                    logger.debug(f"Corrupt packet detected for {key}. Imputing last known value.")
                else:
                    # Absolute fallback
                    cleaned[key] = 9.81 if 'Accel_Z' in key else 0.0
            else:
                cleaned[key] = float(val)
        return cleaned

    def extract_live_features(self) -> pd.DataFrame:
        df_window = pd.DataFrame(self.data_buffer)
        accel_cols = [col for col in ['Accel_X', 'Accel_Y', 'Accel_Z', 'Strain_ue'] if col in df_window.columns]
        
        latest_data = df_window.iloc[-1:].copy()
        
        for col in accel_cols:
            latest_data[f'{col}_roll_std'] = df_window[col].std()
            latest_data[f'{col}_roll_mean'] = df_window[col].mean()
            latest_data[f'{col}_dominant_freq'] = np.argmax(np.abs(np.fft.rfft(df_window[col].values)))
            
        for f in self.feature_names:
            if f not in latest_data.columns:
                latest_data[f] = 0.0  
                
        return latest_data[self.feature_names]

    def process_sensor_tick(self, raw_data_dict: dict):
        # 1. Clean the data FIRST before doing any math
        clean_dict = self._preprocess_tick(raw_data_dict)
        self.data_buffer.append(clean_dict)
        
        if len(self.data_buffer) == self.window_size:
            z_variance = np.var([reading.get('Accel_Z', 0) for reading in self.data_buffer])
            
            if z_variance >= 0.001:
                self.awake_cooldown = 20  
                
            if self.awake_cooldown > 0:
                if not self.is_awake:
                    logger.info(f"⚡ Anomaly spike detected (Var: {z_variance:.4f})! Waking up ML model for FFT analysis...")
                    self.is_awake = True
                
                self.awake_cooldown -= 1
                
                live_features = self.extract_live_features()
                prediction = self.model.predict(live_features)[0]
                
                if prediction > 0:
                    self.handle_actuation(prediction)
            else:
                self.is_awake = False
                return

    def handle_actuation(self, damage_state: int):
        status = f"CRITICAL (State {damage_state}) 🚨"
        
        payload = {
            "sensor_id": "Pillar_A_01",
            "status": status,
            "damage_index": int(damage_state),
            "timestamp": time.time()
        }
        
        logger.warning(f"ACTUATION TRIGGERED: Micro-fracture detected! Closing bridge traffic barrier!")
        logger.info(f"Transmitting emergency payload to Fog Node: {json.dumps(payload)}")
        
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.sendto(json.dumps(payload).encode('utf-8'), ('127.0.0.1', 5005))
        except Exception as e:
            logger.error(f"Failed to transmit to Fog Node: {e}")

# ---------------------------------------------------------
# 3. Stream Simulation Execution (The Bulletproof Demo)
# ---------------------------------------------------------
if __name__ == "__main__":
    current_dir = os.getcwd()
    project_root = os.path.dirname(current_dir) if "edge_node" in current_dir else current_dir
        
    MODEL_PATH = os.path.join(project_root, 'edge_node', 'edge_shm_model.pkl')
    FEATURES_PATH = os.path.join(project_root, 'edge_node', 'model_features.pkl')
    DATA_PATH = os.path.join(project_root, 'data', 'raw', 'sensor_data.csv')
    
    edge_node = BridgeEdgeNode(model_path=MODEL_PATH, features_path=FEATURES_PATH)
    logger.info("Connecting to IoT Sensor Stream...")
    logger.info("⚙️ Initializing Edge-Level Data Imputation Engine...")
    logger.info("⚙️ Initializing Closed-Loop Adaptive Sampling Rate (ASR) engine...")
    
    try:
        df_full = pd.read_csv(DATA_PATH)
        
        # Clean headers
        rename_map = {
            'Temp_C': 'Temp_C', 'Temp (°C)': 'Temp_C', 'Temp (\u00c2\u00b0C)': 'Temp_C',
            'Strain (\u03bc\u03b5)': 'Strain_ue', 'Strain (\u00ce\u00bc\u00ce\u00b5)': 'Strain_ue',
            'Accel_Z (m/s^2)': 'Accel_Z', 'Accel_Y (m/s^2)': 'Accel_Y', 'Accel_X (m/s^2)': 'Accel_X',
            'Condition Label': 'Target'
        }
        df_full = df_full.rename(columns=rename_map)

        # --- CREATE A BULLETPROOF DEMO SCENARIO ---
        df_demo_start = df_full.head(45).copy()
        
        # Force the system back to baseline sleep to get the perfect cinematic ending
        safe_data = {
            'Accel_X': [0.01] * 40,
            'Accel_Y': [0.01] * 40,
            'Accel_Z': [9.81] * 40, # Standard gravity, no variance = Instant Sleep
            'Strain_ue': [50.0] * 40,
            'Temp_C': [25.0] * 40
        }
        df_safe_end = pd.DataFrame(safe_data)
        
        df_demo = pd.concat([df_demo_start, df_safe_end]).reset_index(drop=True)
        df_demo = df_demo.drop(columns=['Timestamp', 'Target'], errors='ignore')
        
        print(f"\n--- STARTING LIVE STREAM (Scenario: Heavy truck crossing) ---")
        
        current_sampling_rate = "LOW (10Hz)"
        
        for index, row in df_demo.iterrows():
            sensor_packet = row.to_dict()
            edge_node.process_sensor_tick(sensor_packet)
            
            if edge_node.is_awake and current_sampling_rate == "LOW (10Hz)":
                logger.warning("⚙️ ASR COMMAND: Throttling sensor UP to 100Hz High-Fidelity Mode for FFT!")
                current_sampling_rate = "HIGH (100Hz)"
                
            elif not edge_node.is_awake and current_sampling_rate == "HIGH (100Hz)":
                logger.info("✅ ⚙️ ASR COMMAND: Threat passed. Cooldown complete. Throttling sensor DOWN to 10Hz Power-Saving Mode.")
                current_sampling_rate = "LOW (10Hz)"
            
            if current_sampling_rate == "LOW (10Hz)" and index % 10 == 0:
                logger.info("🟢 System Idle: Monitoring Bridge Baseline (10Hz)")
            
            sleep_time = 0.05 if current_sampling_rate == "HIGH (100Hz)" else 0.2
            time.sleep(sleep_time) 
            
        print("--- END OF DEMO STREAM ---")
                
    except FileNotFoundError:
        logger.error("Could not find raw data to simulate stream. Check path.")