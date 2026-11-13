import os
import sys
import json
import time
import argparse
from datetime import datetime

# Load environment variables if .env exists
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from modules.deduplicator import Deduplicator
from modules.github_harvester import GitHubHarvester
from modules.yt_channel_dumper import YouTubeDumper
from integrations.telegram_bot import TelegramNotifier
from integrations.github_pusher import GitHubPusher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    cfg_path = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def resolve_path(rel_path):
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(BASE_DIR, rel_path)

def print_banner():
    print("""
===============================================================
       OMNI-SCRIPT-HARVESTER // TITAN AUTONOMOUS ENGINE
   [ Panen Massal Script WhatsApp Bot & Auto-Staging Vault ]
===============================================================
    """)

def run_github_harvest(config, dedup, notifier):
    print("\n[+] Memulai Panen Massal dari GitHub...")
    q_dir = resolve_path(config.get("harvest_settings", {}).get("quarantine_dir", "storage/quarantine_vault"))
    harvester = GitHubHarvester(
        quarantine_dir=q_dir,
        github_token=os.environ.get("GITHUB_TOKEN")
    )
    queries = config.get("github_queries", ["whatsapp bot baileys"])
    total_new = 0

    for q in queries:
        print(f" -> Memindai Query: '{q}'...")
        results = harvester.search_and_harvest(
            query=q, 
            limit=config.get("harvest_settings", {}).get("max_github_results", 5),
            deduplicator=dedup
        )
        print(f"    Ditemukan {len(results)} script baru.")
        for r in results:
            print(f"    [+] Terunduh: {r['local_filename']} ({r['file_size'] / (1024*1024):.2f} MB)")
            notifier.send_harvest_alert(r)
            total_new += 1
        time.sleep(2) # Politeness delay

    notifier.send_batch_summary(total_new, "GitHub Harvester")
    print(f"\n[OK] Selesai! Berhasil mengumpulkan {total_new} script baru dari GitHub.")
    return total_new

def run_youtube_harvest(config, dedup, notifier):
    print("\n[+] Memulai Panen Video Script dari YouTube...")
    q_dir = resolve_path(config.get("harvest_settings", {}).get("quarantine_dir", "storage/quarantine_vault"))
    dumper = YouTubeDumper(
        quarantine_dir=q_dir
    )
    keywords = config.get("youtube_keywords", ["share script bot wa terbaru"])
    total_new = 0

    for kw in keywords:
        print(f" -> Memindai YouTube Keyword: '{kw}'...")
        videos = dumper.search_videos(
            keyword=kw, 
            limit=config.get("harvest_settings", {}).get("max_youtube_results", 3)
        )
        print(f"    Menemukan {len(videos)} video potensial.")
        for v in videos:
            res = dumper.inspect_and_harvest(v["video_id"], deduplicator=dedup)
            if res:
                print(f"    [+] Terpanen: {res['title'][:50]}... | Link: {res['download_url'][:40]}")
                notifier.send_harvest_alert(res)
                total_new += 1
            time.sleep(1.5)

    notifier.send_batch_summary(total_new, "YouTube Dumper")
    print(f"\n[OK] Selesai! Berhasil menjaring {total_new} script dari YouTube.")
    return total_new

def show_status(dedup):
    total = dedup.count_total()
    items = dedup.get_all_harvested(limit=15)
    print(f"\n[STATUS DATABASE] Total script terpanen di vault: {total}")
    print("-" * 65)
    for it in items:
        sz = f"{it['file_size'] / (1024*1024):.2f} MB" if it['file_size'] else "Link Only"
        print(f"• [{it['source'].upper()}] {it['title'][:40]} | {sz} | Status: {it['audit_status']}")
    print("-" * 65)

def main():
    print_banner()
    config = load_config()
    db_path = resolve_path(config.get("harvest_settings", {}).get("db_path", "storage/harvest_history.sqlite"))
    dedup = Deduplicator(db_path=db_path)
    notifier = TelegramNotifier()
    pusher = GitHubPusher(repo_path=BASE_DIR)

    parser = argparse.ArgumentParser(description="OMNI-SCRIPT-HARVESTER CLI")
    parser.add_argument("--github", action="store_true", help="Jalankan panen dari GitHub")
    parser.add_argument("--youtube", action="store_true", help="Jalankan panen dari YouTube")
    parser.add_argument("--all", action="store_true", help="Panen dari semua sumber")
    parser.add_argument("--status", action="store_true", help="Tampilkan status database vault")
    args = parser.parse_args()

    if args.github:
        run_github_harvest(config, dedup, notifier)
        pusher.export_manifest(dedup.get_all_harvested())
        return
    elif args.youtube:
        run_youtube_harvest(config, dedup, notifier)
        pusher.export_manifest(dedup.get_all_harvested())
        return
    elif args.all:
        run_github_harvest(config, dedup, notifier)
        run_youtube_harvest(config, dedup, notifier)
        pusher.export_manifest(dedup.get_all_harvested())
        return
    elif args.status:
        show_status(dedup)
        return

    # Mode Menu Interaktif jika dijalankan tanpa argumen
    while True:
        print("\nPilih Operasi:")
        print("1. Panen Massal dari GitHub API (Rekomendasi Cepat)")
        print("2. Panen Script dari YouTube (Ekstraksi MediaFire / Drive)")
        print("3. Panen Lengkap (GitHub + YouTube)")
        print("4. Cek Status Vault & Daftar Script Karantina")
        print("5. Keluar")
        
        choice = input("\nMasukkan pilihan [1-5]: ").strip()
        if choice == "1":
            run_github_harvest(config, dedup, notifier)
            pusher.export_manifest(dedup.get_all_harvested())
        elif choice == "2":
            run_youtube_harvest(config, dedup, notifier)
            pusher.export_manifest(dedup.get_all_harvested())
        elif choice == "3":
            run_github_harvest(config, dedup, notifier)
            run_youtube_harvest(config, dedup, notifier)
            pusher.export_manifest(dedup.get_all_harvested())
        elif choice == "4":
            show_status(dedup)
        elif choice == "5":
            print("\nSampai jumpa, Sir!")
            break
        else:
            print("Pilihan tidak valid, silakan ulangi.")

if __name__ == "__main__":
    main()
