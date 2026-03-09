import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os

# ---------------------------------------------------------
# 1. Cloud Layer Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CLOUD ANALYTICS] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class BridgeCloudDashboard:
    def __init__(self, data_path: str):
        self.data_path = data_path
        logger.info(f"Initializing Cloud Dashboard with data from: {self.data_path}")

    def generate_report(self):
        """Reads aggregated Fog data and generates a visualization report."""
        if not os.path.exists(self.data_path):
            logger.error("No aggregated data found. Run the Edge and Fog nodes first to populate the cloud storage.")
            return

        # Load the data synced from the Fog node
        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df)} aggregated records from Fog storage.")

        # Convert timestamp to a readable datetime
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values(by='datetime')

        self._plot_degradation_trend(df)

    def _plot_degradation_trend(self, df: pd.DataFrame):
        """Generates a graph showing structural health events over time."""
        logger.info("Generating structural health trend visualization...")
        
        plt.figure(figsize=(12, 6))
        
        # Plotting the damage index over time
        sns.lineplot(data=df, x='datetime', y='damage_index', marker='o', color='red', alpha=0.7)
        
        # Formatting the chart to look professional
        plt.title('Bridge Structural Health Degradation Over Time (Aggregated from Fog Node)', fontsize=14, pad=15)
        plt.xlabel('Timestamp (UTC)', fontsize=12)
        plt.ylabel('Damage Severity Index (0=Safe, 1=Warning, 2=Critical)', fontsize=12)
        plt.yticks([0, 1, 2], ['Safe (0)', 'Warning (1)', 'Critical (2)'])
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        # Save the visualization to the cloud folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_dir, 'bridge_health_report.png')
        
        plt.savefig(save_path, dpi=300)
        logger.info(f"✅ Dashboard report successfully saved to: {save_path}")
        
        # Display the plot
        plt.show()

if __name__ == "__main__":
    # Dynamically find the path to the synced data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(current_dir, 'aggregated_bridge_health.csv')
    
    dashboard = BridgeCloudDashboard(data_path=data_file)
    dashboard.generate_report()