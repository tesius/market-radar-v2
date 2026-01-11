import os

file_path = "/Users/glen/Documents/Project/market-radar/backend/.venv/lib/python3.9/site-packages/yfinance/calendars.py"

try:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if patch needed
    if "list[Any] | list" in content:
        print("Patching yfinance/calendars.py...")
        # Add import if missing
        if "from typing import" not in content:
             # Basic injection, dangerous if not careful but necessary
             pass
        
        # Actually, let's just replace the specific line
        # Original: def __init__(self, operator: str, operand: list[Any] | list["CalendarQuery"]):
        # New: def __init__(self, operator: str, operand: "list[Any] | list[\"CalendarQuery\"]"): 
        # Or better: from typing import Union ... Union[list[Any], list["CalendarQuery"]]
        
        # Simplest: remove type hint or stringify it?
        # Converting to string is safest if we don't want to mess with imports
        # But 'list[Any]' might also be an issue if 'list' is not subscriptable in 3.8 (but 3.9 it is).
        # Python 3.9 allows list[int].
        # But '|' is the issue.
        
        patched_content = content.replace("list[Any] | list[\"CalendarQuery\"]", "Union[list[Any], list[\"CalendarQuery\"]]")
        
        # We also need to make sure Union is imported.
        if "from typing import" in patched_content:
             # append Union to existing import ?? hard to regex safely
             # Add a new line at top
             patched_content = "from typing import Union\n" + patched_content
        else:
             patched_content = "from typing import Union\n" + patched_content
             
        with open(file_path, 'w') as f:
            f.write(patched_content)
        print("Success: Patched.")
    else:
        print("Already patched or pattern not found.")
        
except Exception as e:
    print(f"Error: {e}")
