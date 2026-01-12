import os
import json
import gcsfs
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# --- AUTHENTICATION ---
# (Same logic as before to handle local vs GitHub modes)
key_filename = 'gcp_key.json'
if os.path.exists(key_filename):
    print("Using local key.")
elif 'GCP_SA_KEY' in os.environ:
    print("Using GitHub Secret.")
    with open(key_filename, 'w') as f:
        json.dump(json.loads(os.environ['GCP_SA_KEY']), f)
else:
    raise ValueError("No GCP Key found.")

# --- SETUP & DATA ---
fs = gcsfs.GCSFileSystem(token=key_filename)
bucket_path = 'gs://weathernext/weathernext_2_0_0/zarr'
store = gcsfs.GCSMap(bucket_path, gcs=fs, check=False)
ds = xr.open_zarr(store)

# Select variable (2m Temperature) and region (US/Europe slice)
# Note: WeatherNext usually has 6-hour intervals (0, 6, 12, ... 48)
subset = ds['2m_temperature'].sel(
    latitude=slice(60, 20),
    longitude=slice(-130, -60)
)

# Create output directory
os.makedirs("images", exist_ok=True)

# --- LOOP & PLOT ---
# We loop through the first 12 time steps (approx 48-72 hours depending on interval)
for i in range(12):
    # Select specific time slice
    data_slice = subset.isel(time=i)
    valid_time = data_slice.time.values
    
    # Setup Plot
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.gridlines(draw_labels=False, color='gray', alpha=0.5)

    # Plot Data
    # Convert Kelvin to Celsius for display: .values - 273.15
    temp_c = data_slice.values - 273.15
    
    mesh = ax.pcolormesh(
        data_slice.longitude, 
        data_slice.latitude, 
        temp_c,
        transform=ccrs.PlateCarree(),
        cmap='turbo',
        vmin=-20, vmax=40
    )
    
    plt.colorbar(mesh, label='Temperature (°C)', orientation='vertical', pad=0.02, shrink=0.8)
    
    # Add Title with Valid Time
    # Formats the numpy datetime to a readable string
    time_str = str(valid_time).split('.')[0] 
    plt.title(f"WeatherNext 2 Forecast\nValid: {time_str} UTC", loc='left', fontsize=14)
    plt.title(f"T+{i*6}h", loc='right', fontsize=14, color='blue') # Assuming 6h steps

    # Save with sequential filename (frame_01.png, frame_02.png...)
    filename = f"images/frame_{i+1:02d}.png"
    plt.savefig(filename, bbox_inches='tight', dpi=100)
    plt.close()
    
    print(f"Saved {filename}")

print("All frames generated.")
