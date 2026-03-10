import socket
import json
import logging
import pandas as pd
import os
import time

# ---------------------------------------------------------
# 1. Fog Node Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [FOG GATEWAY] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 2. Fog Aggregator Class (UDP Server)
# ---------------------------------------------------------
class BridgeFogNode:
    def __init__(self, host='127.0.0.1', port=5005):
        self.host = host
        self.port = port
        self.cloud_data_buffer = []
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        
        logger.info(f"Fog Node booted. Listening for Edge devices on UDP {self.host}:{self.port}...")

    def listen_and_aggregate(self):
        alert_counter = 0
        
        try:
            while True:
                # Receive UDP packet
                data, addr = self.sock.recvfrom(1024)
                payload = json.loads(data.decode('utf-8'))
                
                damage_index = payload.get('damage_index', 0)
                sensor_id = payload.get('sensor_id', 'Unknown')
                
                self.cloud_data_buffer.append(payload)
                
                # Fog-Level Logic
                if damage_index > 0:
                    alert_counter += 1
                    logger.warning(f"Hazard Alert from {sensor_id}: STATE {damage_index}")
                    
                    if alert_counter >= 5:
                        logger.critical("🚨 MULTIPLE FAILURES DETECTED! INITIATING FULL REGIONAL BRIDGE LOCKDOWN! 🚨")
                        alert_counter = 0 
                else:
                    alert_counter = max(0, alert_counter - 1)
                    # Visible Heartbeat so you know the network works!
                    logger.info(f"💓 Heartbeat received from {sensor_id} (Status: SAFE). Buffer: {len(self.cloud_data_buffer)}/10")

                # Cloud Synchronization (Lowered to 10 for the demo)
                if len(self.cloud_data_buffer) >= 10:
                    self.sync_to_cloud()
                    
        except KeyboardInterrupt:
            logger.info("Fog Node shutting down...")
        finally:
            self.sock.close()

    def sync_to_cloud(self):
        logger.info("Batching 10 records... Synchronizing with DoT Cloud Storage...")
        
        current_dir = os.getcwd()
        project_root = os.path.dirname(current_dir) if "fog_node" in current_dir else current_dir
        cloud_dir = os.path.join(project_root, 'cloud_layer')
        os.makedirs(cloud_dir, exist_ok=True)
        
        cloud_file = os.path.join(cloud_dir, 'aggregated_bridge_health.csv')
        df_batch = pd.DataFrame(self.cloud_data_buffer)
        
        if not os.path.isfile(cloud_file):
            df_batch.to_csv(cloud_file, index=False)
        else:
            df_batch.to_csv(cloud_file, mode='a', header=False, index=False)
            
        self.cloud_data_buffer = []
        logger.info(f"✅ Cloud sync complete. Data appended to {cloud_file}")

if __name__ == "__main__":
    fog_gateway = BridgeFogNode()
    fog_gateway.listen_and_aggregate()