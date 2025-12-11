from huggingface_hub import list_repo_files
import sys

def check_repo(repo_id):
    print(f"Checking repo: {repo_id}")
    try:
        files = list_repo_files(repo_id)
        print(f"Found {len(files)} files.")
        gguf_files = [f for f in files if f.endswith('.gguf')]
        if gguf_files:
            print("GGUF files found:")
            for f in gguf_files:
                print(f" - {f}")
        else:
            print("No GGUF files found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    repos = [
        "Ans0nWr0ng/llama3.1-8b-cantonese_gguf_v3"
    ]
    
    for repo in repos:
        check_repo(repo)
        print("-" * 20)
