# python backend/agents/repo_loader.py 
from git import Repo
import os
import shutil

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

# Example usage
if __name__ == "__main__":
    repo_url = "https://github.com/id-Software/Quake.git" 
    path = clone_github_repo(repo_url)
