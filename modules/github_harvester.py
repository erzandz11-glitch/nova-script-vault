import urllib.request
import urllib.parse
import json
import os
import re
from datetime import datetime

class GitHubHarvester:
    def __init__(self, quarantine_dir="storage/quarantine_vault", github_token=None):
        self.quarantine_dir = quarantine_dir
        self.github_token = github_token
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def search_and_harvest(self, query: str, limit: int = 5, deduplicator = None):
        """
        Mencari repositori di GitHub dan mengunduh ZIP arsip ke folder karantina.
        """
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=updated&order=desc&per_page={limit}"
        
        headers = {
            "User-Agent": "OMNI-Script-Harvester/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[GitHubHarvester] Error searching for '{query}': {e}")
            return []

        items = data.get("items", [])
        harvested_results = []

        for item in items:
            repo_id = f"github:{item['full_name']}"
            if deduplicator and deduplicator.is_harvested(repo_id):
                continue

            full_name = item["full_name"]
            default_branch = item.get("default_branch", "main")
            zip_url = f"https://github.com/{full_name}/archive/refs/heads/{default_branch}.zip"
            
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', full_name)
            date_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"GH_{clean_name}_{date_tag}.zip"
            dest_path = os.path.join(self.quarantine_dir, filename)

            # Unduh berkas ZIP resmi
            success = self._download_file(zip_url, dest_path)
            file_size = os.path.getsize(dest_path) if success and os.path.exists(dest_path) else 0

            record = {
                "id": repo_id,
                "source": "github",
                "title": item.get("description") or item["name"],
                "author": item["owner"]["login"],
                "source_url": item["html_url"],
                "download_url": zip_url,
                "local_filename": filename,
                "file_size": file_size,
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "license": item.get("license", {}).get("name") if item.get("license") else "No License"
            }

            if deduplicator and success:
                deduplicator.record_harvest(
                    script_id=repo_id,
                    source="github",
                    title=record["title"],
                    author=record["author"],
                    source_url=record["source_url"],
                    download_url=record["download_url"],
                    local_filename=record["local_filename"],
                    file_size=record["file_size"],
                    notes=f"Stars: {record['stars']} | License: {record['license']}"
                )

            harvested_results.append(record)

        return harvested_results

    def _download_file(self, url: str, dest_path: str) -> bool:
        headers = {"User-Agent": "OMNI-Script-Harvester/1.0"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out_file:
                chunk = resp.read(1024 * 64)
                while chunk:
                    out_file.write(chunk)
                    chunk = resp.read(1024 * 64)
            return True
        except Exception as e:
            print(f"[GitHubHarvester] Download failed for {url}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
