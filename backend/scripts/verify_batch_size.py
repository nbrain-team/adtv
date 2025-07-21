#!/usr/bin/env python3
"""Verify the current batch size setting"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtor_importer import tasks

print(f"""
=== BATCH SIZE VERIFICATION ===

Current BATCH_SIZE: {tasks.BATCH_SIZE}

Expected: 20 (new)
Old value: 50

If this shows 50, the deployment hasn't taken effect yet.
If this shows 20, the fix is active!
""") 