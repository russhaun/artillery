import subprocess
import re

def check_route(destination)->bool:
    """Checks if a route exists in the Windows routing table."""
    try:
        # Run the route print command
        result = subprocess.check_output("route print", shell=True).decode('utf-8')
        
        # Search for the specific destination in the output
        if re.search(f"{destination}\s+", result):
            print(f"Route to {destination} found.",flush=True)
            return True
        else:
            print(f"Route to {destination} not found.",flush=True)
            return False
    except Exception as e:
        print(f"Error checking route: {e.with_traceback()}")
        return False
