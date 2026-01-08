import time
import logging
from src.crew import SREOrchestrator
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    orchestrator = SREOrchestrator()
    
    # Configuration
    # We use .get() here safely because these are environment variables or defaults,
    # not the strict config file settings we enforce in crew.py
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 60))
    SLO_INTERVAL = int(os.getenv("SLO_INTERVAL", 300))
    
    last_slo_check = 0
    
    logging.info("🚀 SRE Autonomous Crew Started")

    while True:
        current_time = time.time()
        
        # --- 1. Continuous Monitoring ---
        logging.info("Running Monitor Check...")
        try:
            status = orchestrator.run_monitor()
            status_text = str(status).upper()
            
            logging.info(f"Monitor Output: {status_text}")
            
            # --- ROBUST CONDITION LOGIC ---
            # 1. Explicit Anomaly: The metrics are bad.
            # 2. Tool Error: Prometheus is down or query failed.
            # 3. Fail-Safe: If the agent didn't explicitly say "HEALTHY", assume something is wrong.
            
            is_anomaly = "ANOMALY" in status_text
            is_error = "ERROR" in status_text or "EXCEPTION" in status_text or "FAILED" in status_text
            is_not_healthy = "HEALTHY" not in status_text

            if is_anomaly or is_error or is_not_healthy:
                logging.warning(f"🔥 Incident Detected! (Anomaly={is_anomaly}, Error={is_error}, Unclear={is_not_healthy})")
                logging.warning("Triggering Investigator...")
                
                # Pass the raw status to the investigator so they see the error message
                investigation_result = orchestrator.run_investigation(context=status)
                logging.info(f"Investigation Result: {investigation_result}")
            else:
                logging.info("✅ System Healthy. No action taken.")
                
        except Exception as e:
            # This catches python crashes (e.g., Monitor Agent totally failed to run)
            logging.error(f"CRITICAL: Monitor Loop Crashed: {e}")
            # In a real scenario, you might want to alert here too if the loop keeps crashing
            
        # --- 3. SLO Monitoring (Interval Based) ---
        if current_time - last_slo_check > SLO_INTERVAL:
            logging.info("📉 Running Scheduled SLO Audit...")
            try:
                slo_report = orchestrator.run_slo_check()
                logging.info(f"SLO Report:\n{slo_report}")
                last_slo_check = current_time
            except Exception as e:
                logging.error(f"Error in SLO Loop: {e}")

        time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    import os # Ensure os is imported for the defaults above
    main()
