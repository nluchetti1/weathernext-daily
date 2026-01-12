import ee
import os
import json
import requests
from google.oauth2.service_account import Credentials

# --- 1. AUTHENTICATE ---
SCOPES = ['https://www.googleapis.com/auth/earthengine']

# Handle authentication for both Local (file) and GitHub Actions (Secret env var)
if os.path.exists('gcp_key.json'):
    print("Using local key file.")
    creds = Credentials.from_service_account_file('gcp_key.json', scopes=SCOPES)
elif 'GCP_SA_KEY' in os.environ:
    print("Using GitHub Secret.")
    info = json.loads(os.environ['GCP_SA_KEY'])
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
else:
    raise ValueError("No Service Account Key found. Please set GCP_SA_KEY secret.")

# Initialize Earth Engine
ee.Initialize(credentials=creds)

# --- 2. CONFIGURATION ---
# The exact ID from the link you provided
COLLECTION_ID = 'projects/gcp-public-data-weathernext/assets/weathernext_2_0_0'
REGION = ee.Geometry.Rectangle([-125, 24, -66, 50]) # Continental US
OUTPUT_DIR = "images"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 3. FIND LATEST RUN ---
print("Searching for latest forecast run...")
collection = ee.ImageCollection(COLLECTION_ID)

# We sort by 'start_time' (the run time) descending to find the newest one
# We filter for just one member initially to speed up the "find latest" query
latest_ref = collection.filter(ee.Filter.eq('ensemble_member', '0')) \
                       .sort('start_time', False) \
                       .first()

# Extract the exact string for the start time (e.g., "2024-05-20T00:00:00Z")
latest_start_time = latest_ref.get('start_time').getInfo()
print(f"Latest available run: {latest_start_time}")

# --- 4. PREPARE THE FORECAST ---
# Now we filter the whole collection to:
# 1. The specific run we found above
# 2. A specific ensemble member (using '0' as the control member)
# 3. Sort by forecast_hour (lead time)
forecast_series = collection \
    .filter(ee.Filter.eq('start_time', latest_start_time)) \
    .filter(ee.Filter.eq('ensemble_member', '0')) \
    .sort('forecast_hour')

# We'll fetch the first 12 frames (approx 3 days if 6h steps)
# The documentation says steps are 6 hours.
count = 12
forecast_list = forecast_series.toList(count)

# --- 5. VISUALIZATION PARAMETERS ---
# 2m_temperature is in Kelvin. 
# 250K = -23C (-9F), 310K = 37C (98F)
vis_params = {
    'min': 250,
    'max': 310,
    'palette': [
        '000080', '0000D9', '4000FF', '8000FF', '0080FF', '00FFFF', # Blues/Cold
        '00FF80', '80FF00', 'DAFF00', 'FFFF00', 'FFF500', 'FFDA00', # Greens/Yellows
        'FFB000', 'FF7300', 'FF0000', '800000'                        # Reds/Hot
    ],
    'bands': ['2m_temperature']
}

# --- 6. GENERATE IMAGES ---
print(f"Generating {count} frames...")

for i in range(count):
    try:
        # Get image from list (server-side list to client-side object)
        img = ee.Image(forecast_list.get(i))
        
        # Get metadata for the title/filename
        f_hour = img.get('forecast_hour').getInfo()
        
        # Generate the PNG URL
        url = img.visualize(**vis_params).getThumbURL({
            'region': REGION,
            'dimensions': 1000,
            'format': 'png'
        })
        
        # Download
        response = requests.get(url)
        filename = f"{OUTPUT_DIR}/frame_{i+1:02d}.png"
        
        with open(filename, "wb") as f:
            f.write(response.content)
            
        print(f"Saved Frame {i+1} (Forecast Hour +{f_hour})")
        
    except Exception as e:
        print(f"Error skipping frame {i}: {e}")

print("Update Complete.")
