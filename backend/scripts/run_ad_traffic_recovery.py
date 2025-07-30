#!/usr/bin/env python3
"""
Run ad traffic recovery - fix columns and recover data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_recovery():
    """Run the recovery process"""
    try:
        # Step 1: Fix database columns
        logger.info("Step 1: Fixing database columns...")
        result = subprocess.run([sys.executable, "scripts/fix_database_columns.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Column fix failed: {result.stderr}")
            return False
        logger.info("✅ Database columns fixed")
        
        # Step 2: Check current data
        logger.info("\nStep 2: Checking current ad traffic data...")
        result = subprocess.run([sys.executable, "scripts/check_ad_traffic_data.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        # Step 3: Recover data if needed
        logger.info("\nStep 3: Running data recovery...")
        result = subprocess.run([sys.executable, "scripts/recover_ad_traffic_data.py"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Data recovery failed: {result.stderr}")
            return False
        print(result.stdout)
        
        logger.info("\n✅ Ad Traffic recovery completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Recovery failed: {e}")
        return False

if __name__ == "__main__":
    success = run_recovery()
    sys.exit(0 if success else 1) 