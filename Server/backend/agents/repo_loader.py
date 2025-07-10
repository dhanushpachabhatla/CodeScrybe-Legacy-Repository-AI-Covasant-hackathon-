# python backend/agents/repo_loader.py 
from git import Repo
import os
import shutil
import requests
from urllib.parse import urlparse

def clone_github_repo(repo_url, destination_folder="cloned_repos"):
    try:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_path = os.path.join(destination_folder, repo_name)

        # Remove existing repo if already cloned
        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        # Clone the repository
        print(f"Cloning {repo_url} into {target_path}")
        Repo.clone_from(repo_url, target_path)

        print(" Cloning complete.")
        return target_path

    except Exception as e:
        print(f" Failed to clone repo: {e}")
        return None

def is_valid_github_repo(repo_url: str) -> bool:
    try:
        parsed = urlparse(repo_url)
        if 'github.com' not in parsed.netloc:
            return False

        parts = parsed.path.strip('/').split('/')
        if len(parts) < 2:
            return False

        owner, repo = parts[0], parts[1].replace(".git", "")
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        response = requests.get(api_url)
        return response.status_code == 200
    except Exception:
        return False

# Example usage
if __name__ == "__main__":
    repo_url = "https://github.com/alandipert/ncsa-mosaic.git" 
    path = clone_github_repo(repo_url)
