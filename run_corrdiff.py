import requests
import numpy as np
import matplotlib.pyplot as plt
import os
import json

# --- CONFIGURATION ---
# YOUR KEY (Added as requested - PLEASE ROTATE THIS LATER)
API_KEY = "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"

# NVIDIA CorrDiff Endpoint
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/corrdiff"

# --- 1. SETUP HEADERS ---
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

# --- 2. PREPARE PAYLOAD ---
# Since we cannot generate a 38-variable GFS tensor on a GitHub runner (it's too big),
# we will ask the API to run one of its "Pre-computed" test cases first.
# This verifies your pipeline works.
payload = {
    "time_index": 0,  # Runs the latest available test case
    "channel": "maximum_radar_reflectivity" # The output we want
}

print("Contacting NVIDIA API...")

try:
    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"API Error {response.status_code}: {response.text}")
        exit(1)
        
    print("Success! Received Inference Data.")
    data = response.json()
    
    # --- 3. PROCESS THE OUTPUT ---
    # The API returns a flat list we need to reshape into a grid
    raw_values = data['prediction']
    
    # Calculate grid size (Square root of total pixels)
    # usually 448x448 for CorrDiff
    side = int(np.sqrt(len(raw_values)))
    grid = np.array(raw_values).reshape((side, side))
    
    print(f"Grid Shape: {grid.shape}")

    # --- 4. PLOT ---
    os.makedirs("images", exist_ok=True)
    
    plt.figure(figsize=(10, 10))
    # 'inferno' is a good colormap for Radar
    plt.imshow(grid, cmap='inferno', origin='lower')
    plt.colorbar(label="Reflectivity (dBZ)")
    
    plt.title(f"NVIDIA CorrDiff Inference\nStatus: Generated via API")
    plt.savefig("images/nvidia_output.png")
    plt.close()
    
    print("Saved images/nvidia_output.png")

except Exception as e:
    print(f"Failed to run: {e}")
    exit(1)
