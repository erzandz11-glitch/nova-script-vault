import unittest
import os
import shutil
import json
import tempfile
import sys

# Tambahkan direktori root proyek ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.deduplicator import Deduplicator
from modules.mediafire_grabber import MediaFireGrabber
from integrations.telegram_bot import TelegramNotifier
from integrations.github_pusher import GitHubPusher

class TestOmniScriptHarvester(unittest.TestCase):
    def setUp(self):
        # Gunakan direktori temporer agar pengujian bersih dan aman
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_history.sqlite")
        self.dedup = Deduplicator(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_deduplicator_happy_path(self):
        """Uji alur normal pencatatan dan pengecekan anti-duplikasi"""
        script_id = "github:test/repo-bot"
        inserted = self.dedup.record_harvest(
            script_id=script_id,
            source="github",
            title="Test WhatsApp Bot Baileys",
            author="tester",
            source_url="https://github.com/test/repo-bot",
            download_url="https://github.com/test/repo-bot/archive/main.zip",
            local_filename="test_bot.zip",
            file_size=1024000
        )
        self.assertTrue(inserted, "Record baru harus berhasil disimpan")
        self.assertTrue(self.dedup.is_harvested(script_id), "ID harus terdeteksi sudah pernah dipanen")
        self.assertEqual(self.dedup.count_total(), 1)

    def test_deduplicator_duplicate_edge_case(self):
        """Uji pencegahan duplikasi (id yang sama tidak boleh masuk dua kali)"""
        script_id = "youtube:abc12345678"
        self.dedup.record_harvest(script_id=script_id, source="youtube", title="Video 1")
        # Masukkan lagi dengan ID yang sama
        inserted_again = self.dedup.record_harvest(script_id=script_id, source="youtube", title="Video 1 Duplikat")
        self.assertFalse(inserted_again, "Duplikasi ID harus ditolak")
        self.assertEqual(self.dedup.count_total(), 1)

    def test_telegram_notifier_safe_formatting(self):
        """Uji pembentukan pesan Telegram aman tanpa token aktif (graceful handling)"""
        notifier = TelegramNotifier(bot_token="", chat_id="")
        self.assertFalse(notifier.is_configured(), "Notifier tanpa token harus berstatus tidak aktif")
        # Pengiriman harus return False dengan aman tanpa crash
        alert_result = notifier.send_harvest_alert({
            "source": "github",
            "title": "Bot Baileys <Special & Characters>",
            "author": "dev",
            "local_filename": "bot.zip",
            "file_size": 2048000
        })
        self.assertFalse(alert_result)

    def test_github_pusher_manifest_export(self):
        """Uji pembuatan manifest JSON terstruktur"""
        pusher = GitHubPusher(repo_path=self.test_dir)
        mock_harvested = [
            {"id": "gh:1", "title": "Script 1", "source": "github"},
            {"id": "yt:2", "title": "Script 2", "source": "youtube"}
        ]
        manifest_file = os.path.join(self.test_dir, "manifest.json")
        out = pusher.export_manifest(mock_harvested, output_file=manifest_file)
        
        self.assertTrue(os.path.exists(out))
        with open(out, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["total_scripts"], 2)
            self.assertEqual(len(data["scripts"]), 2)

if __name__ == "__main__":
    unittest.main()
