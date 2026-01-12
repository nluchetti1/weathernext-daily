import os
import json
import gcsfs
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# 1. Setup Authentication using the Secret
# We write the secret to a temporary file because Google Auth expects a file path
service_account_info = json.loads(os.environ['GCP_SA_KEY'])
with open('gcp_key.json', 'w') as f:
    json.dump(service_account_info, f)

# Connect to Google Cloud Storage
fs = gcsfs.GCSFileSystem(token='gcp_key.json')

# 2. Access the Data
# NOTE: Verify the exact bucket path from your Google WeatherNext documentation
bucket_path = 'gs://weathernext/weathernext_2_0_0/zarr' 
store = gcsfs.GCSMap(bucket_path, gcs=fs, check=False)

# Open dataset lazily (doesn't download data yet)
ds = xr.open_zarr(store)

# 3. Slice the Data (CRITICAL STEP)
# GitHub Actions have limited RAM (~7GB). Do NOT load the whole globe.
# Select the latest forecast run, one time step, and one variable (e.g., 2m Temperature)
# Adjust specific variable names based on the dataset metadata (e.g., '2m_temperature', 't2m', etc.)
subset = ds['2m_temperature'].isel(time=0).sel(
    latitude=slice(60, 20),  # Slice for North America/Europe (approx)
    longitude=slice(-130, -60)
)

# 4. Plotting
fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines()
ax.gridlines(draw_labels=True)

# Create the plot
subset.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='coolwarm', cbar_kwargs={'label': 'Temperature (K)'})

plt.title(f"WeatherNext 2 Forecast\nValid: {subset.time.values}")
plt.savefig("forecast.png")
print("Map generated successfully.")
