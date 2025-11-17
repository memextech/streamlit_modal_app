# Running Streamlit
When running streamlit always use with flag `--server.headless=true` to avoid requiring interactive input from user

# Data Sources

## Google Sheets

### CSV Export URL Format
Google Sheets can be accessed as CSV using the export URL format:
```
https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}
```

Where:
- `{SHEET_ID}`: The unique identifier from the sheet URL
- `{GID}`: The specific tab/sheet ID (default is 0)

### SSL Certificate Handling
When loading Google Sheets data with `pandas.read_csv()`, you may encounter SSL certificate verification errors on macOS. Use this pattern to handle it:

```python
import ssl
import urllib.request
import pandas as pd

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load data from Google Sheets"""
    try:
        # Create SSL context that doesn't verify certificates for public Google Sheets
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Fetch data with custom SSL context
        with urllib.request.urlopen(SHEET_URL, context=ssl_context) as response:
            df = pd.read_csv(response)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
```

### Why SSL CERT_NONE is Safe Here
- Reading from public Google Sheets (no sensitive data transmission)
- Google Sheets URLs are read-only CSV exports
- Alternative to installing/configuring system certificates
- Only use for public data sources

### Production Considerations
For production environments with private sheets or sensitive data:
1. Use Google Sheets API with proper OAuth authentication
2. Install proper SSL certificates on the deployment environment
3. Consider caching data locally to reduce API calls
4. Use environment variables for sheet IDs and credentials

# How to deploy Streamlit App to Modal

## Setup Environment
```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install modal streamlit
# Add any other dependencies your app needs
```

## Setup Modal (One-time)
```bash
source .venv/bin/activate && modal setup
```

## Deployment Files
1. Your Streamlit app: `app.py`
2. Modal deployment script: `serve_streamlit.py`

## Modal Deployment Script
Create `serve_streamlit.py`:
```python
import shlex
import subprocess
from pathlib import Path
import modal

# Define file paths
streamlit_script_local_path = Path(__file__).parent / "app.py"
streamlit_script_remote_path = "/root/app.py"

if not streamlit_script_local_path.exists():
    raise RuntimeError(
        "app.py not found! Place the script with your streamlit app in the same directory."
    )

# Container setup with dependencies and local files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "streamlit~=1.35.0",
        # Add your app's dependencies here
    )
    .add_local_file(
        streamlit_script_local_path,
        streamlit_script_remote_path,
    )
)

app = modal.App(name="streamlit-dashboard", image=image)

@app.function()
@modal.concurrent(max_inputs=100)
@modal.web_server(8000)
def run():
    target = shlex.quote(streamlit_script_remote_path)
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true"
    subprocess.Popen(cmd, shell=True)
```

## Deploy
```bash
modal deploy serve_streamlit.py
```

Your app will be available at: `https://[username]--[app-name]-run.modal.run`
