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

# Define container dependencies and add local files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "streamlit~=1.35.0",
        "numpy~=1.26.4",
        "pandas~=2.2.2"
    )
    .add_local_file(
        streamlit_script_local_path,
        streamlit_script_remote_path,
    )
)

app = modal.App(name="streamlit-dashboard", image=image)

# Define the web server function
@app.function()
@modal.concurrent(max_inputs=100)
@modal.web_server(8000)
def run():
    target = shlex.quote(streamlit_script_remote_path)
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true"
    subprocess.Popen(cmd, shell=True)