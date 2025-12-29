import os
from huggingface_hub import hf_hub_download
from pathlib import Path

def download_model():
    repo_id = "Ans0nWr0ng/llama3.1-8b-cantonese_gguf_v3"
    filename = "Llama-cantonese-8.0B-Q4_K_M.gguf"
    
    # Use the same directory as the app
    local_dir = Path.home() / ".canto_beats" / "models"
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"Target directory: {local_dir}")
    print(f"Downloading {filename} from {repo_id}...")
    print("This may take a while (approx 4.8 GB)...")
    
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"\nSUCCESS! Model downloaded to:\n{path}")
    except Exception as e:
        print(f"\nERROR: Download failed: {e}")

if __name__ == "__main__":
    download_model()
