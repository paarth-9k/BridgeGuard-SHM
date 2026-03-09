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
        
        # Setup UDP Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        
        logger.info(f"Fog Node booted. Listening for Edge devices on UDP {self.host}:{self.port}...")

    def listen_and_aggregate(self):
        """Infinite loop listening for Edge node telemetry."""
        alert_counter = 0
        last_summary_time = time.time()
        
        try:
            while True:
                # Receive UDP packet (buffer size 1024 bytes)
                data, addr = self.sock.recvfrom(1024)
                payload = json.loads(data.decode('utf-8'))
                
                # 1. Process incoming packet
                damage_index = payload.get('damage_index', 0)
                sensor_id = payload.get('sensor_id', 'Unknown')
                
                # Append to our cloud buffer
                self.cloud_data_buffer.append(payload)
                
                # 2. Fog-Level Logic (Regional Aggregation)
                if damage_index > 0:
                    alert_counter += 1
                    logger.warning(f"Received Hazard Alert from {sensor_id} (Index: {damage_index})")
                    
                    # If we get 5 alerts in quick succession, trigger the MASTER bridge alarm
                    if alert_counter >= 5:
                        logger.critical("🚨 MULTIPLE FAILURES DETECTED! INITIATING FULL BRIDGE LOCKDOWN! 🚨")
                        alert_counter = 0 # Reset counter after alarm
                else:
                    # If we get safe readings, gradually lower the alert counter
                    alert_counter = max(0, alert_counter - 1)

                # 3. Cloud Synchronization (Simulated: Export every 20 packets)
                if len(self.cloud_data_buffer) >= 20:
                    self.sync_to_cloud()
                    
        except KeyboardInterrupt:
            logger.info("Fog Node shutting down...")
        finally:
            self.sock.close()

    def sync_to_cloud(self):
        """Batches the aggregated data and pushes it to the Cloud Layer storage."""
        logger.info("Batching 20 records... Synchronizing with DoT Cloud Storage...")
        
        # Dynamically find the cloud_layer folder
        current_dir = os.getcwd()
        project_root = os.path.dirname(current_dir) if "fog_node" in current_dir else current_dir
        cloud_dir = os.path.join(project_root, 'cloud_layer')
        os.makedirs(cloud_dir, exist_ok=True)
        
        cloud_file = os.path.join(cloud_dir, 'aggregated_bridge_health.csv')
        
        # Convert buffer to dataframe and append to CSV
        df_batch = pd.DataFrame(self.cloud_data_buffer)
        
        # If file doesn't exist, write headers. Otherwise, append.
        if not os.path.isfile(cloud_file):
            df_batch.to_csv(cloud_file, index=False)
        else:
            df_batch.to_csv(cloud_file, mode='a', header=False, index=False)
            
        # Clear the buffer after successful upload
        self.cloud_data_buffer = []
        logger.info(f"✅ Cloud sync complete. Data appended to {cloud_file}")

# ---------------------------------------------------------
# 3. Execution Block
# ---------------------------------------------------------
if __name__ == "__main__":
    fog_gateway = BridgeFogNode()
    fog_gateway.listen_and_aggregate()