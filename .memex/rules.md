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

## Running Streamlit Locally (Non-blocking)
When testing Streamlit locally, use these approaches to avoid blocking commands:

#### Option 1: Run in background with output redirection
```bash
(streamlit run app.py --server.headless=true > streamlit.log 2>&1 &)
```

#### Option 2: Run with headless mode and specific port
```bash
(streamlit run app.py --server.headless=true --server.port 8501 > streamlit.log 2>&1 &)
```

#### Option 3: First-time setup (avoid email prompt)
Create a .streamlit/credentials.toml file with:
```bash
# [general]
# email = "your-email@example.com"
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

# Container setup with dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "streamlit~=1.35.0",
    # Add your app's dependencies here
)

app = modal.App(name="streamlit-dashboard", image=image)

# Mount app.py
streamlit_script_local_path = Path(__file__).parent / "app.py"
streamlit_script_remote_path = Path("/root/app.py")

streamlit_script_mount = modal.Mount.from_local_file(
    streamlit_script_local_path,
    streamlit_script_remote_path,
)

@app.function(
    allow_concurrent_inputs=100,
    mounts=[streamlit_script_mount],
)
@modal.web_server(8000)
def run():
    cmd = f"streamlit run {streamlit_script_remote_path} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    subprocess.Popen(shlex.split(cmd))

if __name__ == "__main__":
    app.serve()
```

## Deploy
```bash
modal deploy serve_streamlit.py
```

Your app will be available at: `https://[username]--[app-name]-run.modal.run`

## Troubleshooting

### Avoiding Blocking Commands
- Always run Streamlit with the `--server.headless=true` flag to avoid interactive prompts
- Use background processes with `&` and redirect output with `> streamlit.log 2>&1`
- Check if the app is running with `ps aux | grep -i streamlit | grep -v grep`
- View logs with `cat streamlit.log`

### First-time Streamlit Setup
If you encounter interactive prompts asking for email during first-time setup:
1. Create a `.streamlit` directory in your project
2. Create a `credentials.toml` file with:
   ```toml
   [general]
   email = "your-email@example.com"
   ```

### Modal Deployment Issues
- If deployment fails, check Modal logs in the web interface
- Ensure all dependencies are correctly specified in the `serve_streamlit.py` file
- Verify that `app.py` exists and is in the same directory as `serve_streamlit.py`

