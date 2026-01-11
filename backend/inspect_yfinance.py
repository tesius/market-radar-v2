import os

file_path = "/Users/glen/Documents/Project/market-radar/backend/.venv/lib/python3.9/site-packages/yfinance/calendars.py"

try:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    print(f"Inspecting {file_path} for '|' usage:")
    for i, line in enumerate(lines):
        if "|" in line:
            print(f"{i+1}: {line.strip()}")
            
except Exception as e:
    print(f"Error: {e}")
