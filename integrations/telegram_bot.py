import urllib.request
import urllib.parse
import json
import os

class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and "your_bot_token" not in self.bot_token)

    def send_harvest_alert(self, script_info: dict) -> bool:
        """
        Mengirimkan notifikasi laporan script baru yang berhasil terpanen ke Telegram.
        """
        if not self.is_configured():
            return False

        source = script_info.get("source", "Unknown").upper()
        title = script_info.get("title", "No Title")
        author = script_info.get("author", "Komunitas")
        source_url = script_info.get("source_url", "-")
        download_url = script_info.get("download_url", "-")
        filename = script_info.get("local_filename") or "Tersimpan via Link"
        file_size = script_info.get("file_size", 0)
        size_str = f"{file_size / (1024*1024):.2f} MB" if file_size > 0 else "N/A"

        msg = (
            f"🚨 <b>OMNI-HARVESTER: SCRIPT BARU TERDETEKSI!</b>\n\n"
            f"📡 <b>Sumber:</b> {source}\n"
            f"🏷️ <b>Judul:</b> {title}\n"
            f"👤 <b>Author/Channel:</b> {author}\n"
            f"🔗 <b>Tautan Sumber:</b> {source_url}\n"
            f"📥 <b>Link Download:</b> {download_url}\n"
            f"💾 <b>Berkas:</b> <code>{filename}</code> ({size_str})\n\n"
            f"🛡️ <b>Status:</b> Masuk Karantina (Siap Uji OMNI-TITAN)\n"
            f"👉 <i>Buka Antigravity untuk audit & de-obfuscation!</i>"
        )

        return self._send_message(msg)

    def send_batch_summary(self, total_harvested: int, source_name: str) -> bool:
        if not self.is_configured() or total_harvested <= 0:
            return False

        msg = (
            f"🌾 <b>PANEN MASSAL SELESAI ({source_name.upper()})!</b>\n\n"
            f"✅ Berhasil mengumpulkan <b>{total_harvested} script baru</b> ke dalam folder karantina.\n"
            f"📂 Siap diaudit menggunakan OMNI-TITAN di Antigravity."
        )
        return self._send_message(msg)

    def send_audit_summary(self, audit_summary: dict) -> bool:
        """
        Mengirimkan laporan hasil audit keamanan OMNI-TITAN ke Telegram.
        """
        if not self.is_configured():
            return False

        total = audit_summary.get("total", 0)
        verified = audit_summary.get("verified", 0)
        suspicious = audit_summary.get("suspicious", 0)
        rejected = audit_summary.get("rejected", 0)

        msg = (
            f"🔱 <b>OMNI-TITAN AUDIT REPORT PARIPURNA</b>\n\n"
            f"📊 <b>Total Script Diuji:</b> {total}\n"
            f"🟢 <b>Verified Safe (Lolos):</b> {verified}\n"
            f"🟡 <b>Suspicious (Obfuscated):</b> {suspicious}\n"
            f"🔴 <b>Rejected (Backdoor/Rusak):</b> {rejected}\n\n"
            f"🛡️ <i>Semua skrip yang lolos 'Verified Safe' telah disaring dari backdoor/stealer dan siap dipublikasikan ke NOVA Vault!</i>"
        )
        return self._send_message(msg)

    def _send_message(self, html_text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }).encode("utf-8")

        req = urllib.request.Request(
            url, 
            data=payload, 
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[TelegramNotifier] Gagal mengirim pesan: {e}")
            return False
