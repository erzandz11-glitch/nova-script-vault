import subprocess
import json
import os
from datetime import datetime

class GitHubPusher:
    def __init__(self, repo_path=".", staging_branch="staging"):
        self.repo_path = repo_path
        self.staging_branch = staging_branch

    def export_manifest(self, harvested_list: list, output_file="storage/harvested_manifest.json"):
        """
        Mengekspor daftar seluruh script yang terpanen ke file JSON manifest publik.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        manifest_data = {
            "last_updated": datetime.now().isoformat(),
            "total_scripts": len(harvested_list),
            "scripts": harvested_list
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        print(f"[GitHubPusher] Manifest berhasil disimpan ke {output_file}")
        return output_file

    def stage_and_commit(self, commit_message="feat(vault): auto-stage harvested community scripts"):
        """
        Menambahkan perubahan manifest ke git staging jika repo git aktif.
        """
        try:
            # Cek status git
            res = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo_path, capture_output=True, text=True)
            if not res.stdout.strip():
                print("[GitHubPusher] Tidak ada berkas baru untuk di-commit.")
                return False

            subprocess.run(["git", "add", "storage/harvested_manifest.json"], cwd=self.repo_path, check=True)
            subprocess.run(["git", "commit", "-m", commit_message], cwd=self.repo_path, check=True)
            print("[GitHubPusher] Berhasil melakukan commit git staging.")
            return True
        except Exception as e:
            print(f"[GitHubPusher] Lewati git commit (bukan git repository atau tidak ada perubahan): {e}")
            return False
