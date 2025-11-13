"""
Quick Python version check

Run this in USD Composer Script Editor to see what Python version we're using.
"""

import sys
import carb

carb.log_info("=" * 60)
carb.log_info("Omniverse Python Information")
carb.log_info("=" * 60)
carb.log_info(f"Python version: {sys.version}")
carb.log_info(f"Python executable: {sys.executable}")
carb.log_info(f"Python prefix: {sys.prefix}")
carb.log_info("=" * 60)

print("=" * 60)
print("Omniverse Python Information")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python prefix: {sys.prefix}")
print("=" * 60)
