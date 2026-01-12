import requests
import numpy as np
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
# YOUR KEY (Added as requested)
API_KEY = "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"
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/corrdiff"
OUTPUT_DIR = "images"

# Create output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

print(f"Starting batch generation of 12 frames...")

# Loop for 12 frames (approx 12 hours)
for i in range(12):
    # 'time_index' in the Sandbox API usually selects different test cases.
    # In a real production API, you would pass a specific timestamp.
    # For this demo, we increment the index to see different test states if available.
    payload = {
        "time_index": i, 
        "channel": "maximum_radar_reflectivity"
    }

    print(f"Requesting Frame {i+1}...")

    try:
        response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"  Error {response.status_code}: {response.text}")
            continue # Skip this frame if it fails
            
        data = response.json()
        raw_values = data['prediction']
        
        # Reshape (Assuming 448x448)
        side = int(np.sqrt(len(raw_values)))
        grid = np.array(raw_values).reshape((side, side))

        # Plotting
        plt.figure(figsize=(10, 10))
        plt.imshow(grid, cmap='inferno', origin='lower')
        # Add labels
        plt.colorbar(label="Reflectivity (dBZ)")
        plt.title(f"NVIDIA CorrDiff Forecast\nFrame +{i}h")
        
        # Save as sequential filenames for your HTML viewer
        filename = f"{OUTPUT_DIR}/frame_{i+1:02d}.png"
        plt.savefig(filename)
        plt.close()
        
        print(f"  Saved {filename}")

    except Exception as e:
        print(f"  Failed frame {i}: {e}")

print("Batch complete.")
