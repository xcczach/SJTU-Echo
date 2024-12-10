from huggingface_hub import snapshot_download
import os
repo_id="coqui/XTTS-v2"
current_dir = os.path.dirname(os.path.abspath(__file__))
local_dir=os.path.join(current_dir, "xttsv2")
print(f"Downloading {repo_id} to {local_dir}")
if not os.path.exists(local_dir):
    os.makedirs(local_dir)
snapshot_download(repo_id, local_dir=local_dir)