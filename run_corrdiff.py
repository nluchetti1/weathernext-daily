import requests
import numpy as np
import matplotlib.pyplot as plt
import os
import json

# REGENERATE YOUR KEY FIRST!
API_KEY = os.environ.get("NVIDIA_API_KEY")

# --- THE FIX: USE THE SPECIFIC US MODEL ENDPOINT ---
# The previous URL was for the generic (Taiwan) model.
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/corrdiff-us-gefs-hrrr/infer"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

print("Attempting to hit US CorrDiff Endpoint...")

# We will try just ONE frame first to verify access
# We use 'time_index' 0 which maps to the first available test case in the US Sandbox
payload = {
    "time_index": 0,
    "channel": "maximum_radar_reflectivity"
}

try:
    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
    
    # DEBUGGING: Print exact error if it fails
    if response.status_code != 200:
        print(f"FAILED. Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("\nDIAGNOSIS:")
        if response.status_code == 404:
            print("- The 'US' endpoint might be private/enterprise only.")
        elif response.status_code == 402 or response.status_code == 403:
            print("- Your free credits are exhausted or don't apply to this model.")
        else:
            print("- Invalid payload or server error.")
        exit(1)

    print("SUCCESS! We got data.")
    data = response.json()
    
    # Process & Plot
    raw_values = data['prediction']
    side = int(np.sqrt(len(raw_values)))
    grid = np.array(raw_values).reshape((side, side))
    
    os.makedirs("images", exist_ok=True)
    plt.figure(figsize=(10, 10))
    plt.imshow(grid, cmap='inferno', origin='lower')
    plt.colorbar(label="Reflectivity (dBZ)")
    plt.title("NVIDIA CorrDiff US (Free Tier)")
    plt.savefig("images/frame_01.png")
    print("Saved images/frame_01.png")

except Exception as e:
    print(f"Script crashed: {e}")
