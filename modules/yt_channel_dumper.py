import urllib.request
import urllib.parse
import re
import os
import json
from datetime import datetime
from modules.mediafire_grabber import MediaFireGrabber

class YouTubeDumper:
    def __init__(self, quarantine_dir="storage/quarantine_vault"):
        self.quarantine_dir = quarantine_dir
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def search_videos(self, keyword: str, limit: int = 5):
        """
        Mencari video terbaru di YouTube berdasarkan kata kunci (tanpa kuota API).
        """
        encoded_kw = urllib.parse.quote(keyword)
        # sp=CAISAhAB memfilter video terbaru (upload date)
        url = f"https://www.youtube.com/results?search_query={encoded_kw}&sp=CAISAhAB"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[YouTubeDumper] Gagal mencari '{keyword}': {e}")
            return []

        # Ekstrak videoId dari data JSON YouTube
        video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)))
        results = []

        for vid in video_ids[:limit]:
            results.append({
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}"
            })

        return results

    def inspect_and_harvest(self, video_id: str, deduplicator = None):
        """
        Memeriksa halaman video, mengekstrak link unduhan di deskripsi, dan mendownload jika direct.
        """
        script_id = f"youtube:{video_id}"
        if deduplicator and deduplicator.is_harvested(script_id):
            return None

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "id-ID,id;q=0.9"
        }

        try:
            req = urllib.request.Request(video_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[YouTubeDumper] Gagal membuka video {video_id}: {e}")
            return None

        # Ambil judul video
        title_match = re.search(r'<title>(.*?)</title>', html)
        raw_title = title_match.group(1).replace(" - YouTube", "").strip() if title_match else f"Video {video_id}"
        
        # Cari tautan unduhan potensial (Mediafire, Google Drive, GitHub, Shortlink)
        mediafire_links = re.findall(r'https?://(?:www\.)?mediafire\.com/file/[^\s\'"<>\\]+', html)
        gdrive_links = re.findall(r'https?://drive\.google\.com/file/d/[^\s\'"<>\\]+', html)
        github_links = re.findall(r'https?://github\.com/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+', html)
        shortlinks = re.findall(r'https?://(?:sub4unlock|sfl|linkduit|teknosimple|sfile)[^\s\'"<>\\]+', html)

        download_url = None
        is_shortlink = False
        notes = []

        if mediafire_links:
            download_url = mediafire_links[0]
            notes.append("Found MediaFire Link")
        elif github_links:
            download_url = github_links[0]
            notes.append("Found GitHub Link")
        elif gdrive_links:
            download_url = gdrive_links[0]
            notes.append("Found Google Drive Link")
        elif shortlinks:
            download_url = shortlinks[0]
            is_shortlink = True
            notes.append("Shortlink Protected")
        else:
            download_url = video_url
            notes.append("Link di deskripsi perlu dicek manual")

        local_filename = ""
        file_size = 0
        success_download = False

        # Jika mediafire, coba download langsung
        if download_url and "mediafire.com" in download_url:
            clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_title)[:40]
            date_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"YT_{clean_title}_{date_tag}.zip"
            dest_path = os.path.join(self.quarantine_dir, local_filename)

            direct_url = MediaFireGrabber.resolve_direct_url(download_url)
            if direct_url.startswith("http"):
                success_download = MediaFireGrabber.download_file(direct_url, dest_path)
                if success_download and os.path.exists(dest_path):
                    file_size = os.path.getsize(dest_path)

        record = {
            "id": script_id,
            "source": "youtube",
            "title": raw_title,
            "source_url": video_url,
            "download_url": download_url,
            "is_shortlink": is_shortlink,
            "local_filename": local_filename,
            "file_size": file_size,
            "notes": ", ".join(notes)
        }

        if deduplicator:
            deduplicator.record_harvest(
                script_id=script_id,
                source="youtube",
                title=record["title"],
                author="YouTube Community",
                source_url=record["source_url"],
                download_url=record["download_url"],
                local_filename=record["local_filename"],
                file_size=record["file_size"],
                notes=record["notes"]
            )

        return record
