#!/usr/bin/env python3
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import uvicorn
    print(f"uvicorn installed: {uvicorn.__version__}")
except ImportError:
    print("ERROR: uvicorn not installed")

try:
    import sqlalchemy
    print(f"sqlalchemy installed: {sqlalchemy.__version__}")
except ImportError:
    print("ERROR: sqlalchemy not installed")

print("\nPython path:")
for path in sys.path:
    print(f"  {path}") 