import urllib.request
import re
import os

class MediaFireGrabber:
    @staticmethod
    def resolve_direct_url(mediafire_url: str) -> str:
        """
        Mengekstrak URL download langsung dari halaman mediafire.
        """
        try:
            req = urllib.request.Request(
                mediafire_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                
            # Mencari tombol download href
            match = re.search(r'href=[\'"](https?://download\d+\.mediafire\.com/[^\'"]+)[\'"]', html)
            if match:
                return match.group(1)
            
            # Alternatif pola
            match_alt = re.search(r'aria-label=[\'"]Download file[\'"][^>]*href=[\'"]([^\'"]+)[\'"]', html)
            if match_alt:
                return match_alt.group(1)
                
            return mediafire_url
        except Exception as e:
            print(f"[MediaFireGrabber] Error resolving {mediafire_url}: {e}")
            return mediafire_url

    @staticmethod
    def download_file(direct_url: str, dest_path: str) -> bool:
        try:
            req = urllib.request.Request(
                direct_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=40) as resp, open(dest_path, "wb") as out_file:
                chunk = resp.read(1024 * 64)
                while chunk:
                    out_file.write(chunk)
                    chunk = resp.read(1024 * 64)
            return True
        except Exception as e:
            print(f"[MediaFireGrabber] Download failed for {direct_url}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
