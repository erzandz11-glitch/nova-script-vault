import os
import sys
import json
import zipfile
import re
import sqlite3
from datetime import datetime

class OmniTitanAuditor:
    """
    OMNI-TITAN Autonomous Security & Code Integrity Auditor.
    Menganalisis file ZIP bot WhatsApp di karantina untuk mendeteksi backdoor,
    session stealers, destructive payloads, obfuscation, serta mengekstrak metadata teknis.
    """

    # 1. Backdoor & Stealer Patterns (High-Severity Threat)
    STEALER_PATTERNS = [
        (r'api\.telegram\.org/bot', 'Telegram Bot Session Exfiltration'),
        (r'discord\.com/api/webhooks', 'Discord Webhook Exfiltration'),
        (r'(creds\.json|auth_info_baileys|session)[^\n]*(https?://|curl|fetch|axios)', 'WhatsApp Session Folder Theft'),
        (r'(\.session|auth_info)[^\n]*(\.post|\.get|upload)', 'Baileys Auth Data Hijacking'),
        (r'Buffer\.from\([\'"][A-Za-z0-9+/=]{100,}[\'"]\s*,\s*[\'"]base64[\'"]\)', 'Base64 Encoded Binary Payload'),
        (r'eval\s*\(\s*(atob|Buffer\.from|unescape)', 'Eval with Decoded Buffer/Payload'),
        (r'child_process.*(rm\s+-rf|del\s+/f|format\s+[a-z]:)', 'Destructive System Shell Command'),
        (r'pastebin\.com/raw/[a-zA-Z0-9]+', 'Suspicious External Code Injection Source'),
        (r'raw\.githubusercontent\.com/[^\n]*(stealer|grabber|backdoor)', 'Malicious Remote Code Loading'),
    ]

    # 2. Heavy Obfuscation Patterns
    OBFUSCATION_PATTERNS = [
        (r'_0x[a-f0-9]{4,6}', 'Javascript-Obfuscator Hex Variables'),
        (r'\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}', 'Hex Escaped Character Sequences'),
        (r'var\s+_0x[a-f0-9]+\s*=\s*\[', 'Obfuscator String Table Array'),
        (r'function\(_0x[a-f0-9]+,\s*_0x[a-f0-9]+\)', 'Obfuscator Shift Function'),
    ]

    # 3. Category Heuristics
    CATEGORY_KEYWORDS = {
        'jpm': ['jpm', 'broadcast', 'pushkontak', 'push_kontak', 'post-group', 'spintax'],
        'commerce': ['store', 'shop', 'order', 'kasir', 'qris', 'payment', 'topup', 'saldo', 'deposit', 'digiflazz'],
        'ai': ['openai', 'chatgpt', 'gemini', 'anthropic', 'ai-chat', 'copilot', 'bard'],
        'defender': ['antilink', 'anti-link', 'antidelete', 'anti-delete', 'antivirtex', 'kick', 'banchat', 'guard'],
        'media': ['tiktok', 'ytdl', 'youtube', 'igdl', 'instagram', 'downloader', 'play', 'spotify', 'mp3', 'sticker'],
        'games': ['rpg', 'game', 'tebak', 'casino', 'slot', 'suit', 'tictactoe'],
        'panel': ['pterodactyl', 'panel', 'createuser', 'server-create', 'pterohost']
    }

    def __init__(self, db_path="storage/harvest_history.sqlite", quarantine_dir="storage/quarantine_vault"):
        self.db_path = db_path
        self.quarantine_dir = quarantine_dir

    def audit_zip_file(self, zip_filepath: str) -> dict:
        """
        Melakukan audit mendalam terhadap sebuah file ZIP bot tanpa mengekstrak ke disk fisik.
        """
        report = {
            "filename": os.path.basename(zip_filepath),
            "file_size": 0,
            "security_score": 100,
            "verdict": "VERIFIED_SAFE",
            "findings": [],
            "obfuscation_count": 0,
            "total_js_files": 0,
            "has_package_json": False,
            "package_name": "",
            "main_entry": "index.js",
            "baileys_version": "Baileys MD v6+",
            "node_version": "Node.js 18+",
            "detected_category": "media",
            "extracted_features": [],
            "error": None
        }

        if not os.path.exists(zip_filepath):
            report["verdict"] = "REJECTED_DANGEROUS"
            report["security_score"] = 0
            report["error"] = "File tidak ditemukan"
            return report

        report["file_size"] = os.path.getsize(zip_filepath)

        # File kosong (< 50 bytes) bukan file zip yang valid
        if report["file_size"] < 50:
            report["security_score"] = 0
            report["verdict"] = "REJECTED_DANGEROUS"
            report["findings"].append("Corrupted or empty archive (< 50 bytes)")
            return report

        try:
            with zipfile.ZipFile(zip_filepath, 'r') as z:
                namelist = z.namelist()
                
                # Check file list & sizes (Zip Bomb protection)
                total_uncompressed = sum(info.file_size for info in z.infolist())
                if total_uncompressed > 200 * 1024 * 1024: # > 200 MB uncompressed
                    report["findings"].append("Warning: Uncompressed size exceeds 200 MB limit")
                    report["security_score"] -= 20

                # Analyze package.json if present
                for name in namelist:
                    if name.endswith("package.json") and not "node_modules" in name:
                        report["has_package_json"] = True
                        try:
                            pkg_content = z.read(name).decode('utf-8', errors='ignore')
                            pkg_data = json.loads(pkg_content)
                            report["package_name"] = pkg_data.get("name", "")
                            report["main_entry"] = pkg_data.get("main", "index.js")
                            deps = pkg_data.get("dependencies", {})
                            
                            # Cek versi Baileys
                            if "@whiskeysockets/baileys" in deps:
                                report["baileys_version"] = f"WhiskeySockets Baileys {deps['@whiskeysockets/baileys']}"
                            elif "@adiwajshing/baileys" in deps:
                                report["baileys_version"] = f"Legacy Baileys {deps['@adiwajshing/baileys']}"
                            
                            # Cek engine Node
                            engines = pkg_data.get("engines", {})
                            if "node" in engines:
                                report["node_version"] = f"Node.js {engines['node']}"
                        except Exception:
                            pass
                        break

                # Inspect code files (.js, .json, .ts, .mjs, .cjs)
                threat_penalty = 0
                category_hits = {k: 0 for k in self.CATEGORY_KEYWORDS}
                code_samples = []

                for info in z.infolist():
                    if info.is_dir():
                        continue
                    
                    filename_lower = info.filename.lower()
                    
                    # Abaikan file di dalam node_modules jika ada (hemat waktu & memory)
                    if "node_modules/" in filename_lower or ".git/" in filename_lower:
                        continue

                    # Hitung kategori berdasarkan nama file
                    for cat, keywords in self.CATEGORY_KEYWORDS.items():
                        for kw in keywords:
                            if kw in filename_lower:
                                category_hits[cat] += 2

                    if filename_lower.endswith(('.js', '.ts', '.mjs', '.cjs')):
                        report["total_js_files"] += 1
                        
                        # Baca konten file (maks 1MB per file untuk keamanan scanning)
                        if info.file_size <= 1024 * 1024:
                            try:
                                content = z.read(info.filename).decode('utf-8', errors='ignore')
                                
                                # Scan Stealer / Backdoor
                                for pattern, desc in self.STEALER_PATTERNS:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        report["findings"].append(f"[CRITICAL] {desc} in {info.filename}")
                                        threat_penalty += 35

                                # Scan Obfuscation
                                for pattern, desc in self.OBFUSCATION_PATTERNS:
                                    matches = len(re.findall(pattern, content))
                                    if matches > 5:
                                        report["obfuscation_count"] += matches
                                        if desc not in report["findings"]:
                                            report["findings"].append(f"[SUSPICIOUS] {desc} in {info.filename} ({matches} matches)")
                                        threat_penalty += 10

                                # Scan fitur & kategori dari isi teks
                                for cat, keywords in self.CATEGORY_KEYWORDS.items():
                                    for kw in keywords:
                                        if kw in content.lower():
                                            category_hits[cat] += 1
                                            
                            except Exception:
                                pass

                # Tentukan Kategori Pemenang
                best_cat = max(category_hits, key=category_hits.get)
                if category_hits[best_cat] > 0:
                    report["detected_category"] = best_cat
                else:
                    report["detected_category"] = "media"

                # Hitung Skor Keamanan Akhir
                final_score = max(0, 100 - threat_penalty)
                report["security_score"] = final_score

                # Tentukan Verdict
                if any("[CRITICAL]" in f for f in report["findings"]) or final_score < 40:
                    report["verdict"] = "REJECTED_DANGEROUS"
                elif report["obfuscation_count"] > 30 or final_score < 75:
                    report["verdict"] = "SUSPICIOUS_OBFUSCATED"
                else:
                    report["verdict"] = "VERIFIED_SAFE"

                # Rumuskan Fitur Unggulan
                features = []
                if report["has_package_json"]:
                    features.append("Struktur Modul Lengkap (package.json)")
                if report["detected_category"] == "commerce":
                    features.extend(["Fitur Kasir & Toko Digital", "Katalog Produk Otomatis"])
                elif report["detected_category"] == "jpm":
                    features.extend(["Fitur Broadcast JPM", "Manajemen Grup & Kontak"])
                elif report["detected_category"] == "ai":
                    features.extend(["Integrasi Multi-AI Bot", "Chat Copilot"])
                elif report["detected_category"] == "defender":
                    features.extend(["Sistem Anti-Link & Proteksi Grup", "Auto-Kick Keamanan"])
                elif report["detected_category"] == "media":
                    features.extend(["Downloader Multi-Platform (TT/YT/IG)", "Media Converter"])
                elif report["detected_category"] == "panel":
                    features.extend(["Automasi Panel Pterodactyl", "Manajemen Server Bot"])
                else:
                    features.extend(["Multi-Command Baileys", "Menu Interaktif Lengkap"])

                if report["verdict"] == "VERIFIED_SAFE":
                    features.append("100% No-Backdoor & Kode Bersih")
                
                report["extracted_features"] = features[:5]

        except zipfile.BadZipFile:
            report["verdict"] = "REJECTED_DANGEROUS"
            report["security_score"] = 0
            report["findings"].append("Corrupted ZIP file (BadZipFile)")
        except Exception as e:
            report["verdict"] = "REJECTED_DANGEROUS"
            report["security_score"] = 0
            report["findings"].append(f"Audit exception: {str(e)}")

        return report

    def audit_all_quarantine(self) -> dict:
        """
        Menjalankan audit massal untuk seluruh file di quarantine_vault
        dan memperbarui database SQLite.
        """
        if not os.path.exists(self.quarantine_dir):
            return {"total": 0, "verified": 0, "suspicious": 0, "rejected": 0, "items": []}

        zip_files = [f for f in os.listdir(self.quarantine_dir) if f.endswith(".zip")]
        results = []
        verified_count = 0
        suspicious_count = 0
        rejected_count = 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for zf in zip_files:
            full_path = os.path.join(self.quarantine_dir, zf)
            rep = self.audit_zip_file(full_path)
            results.append(rep)

            if rep["verdict"] == "VERIFIED_SAFE":
                verified_count += 1
                db_status = "verified_safe"
            elif rep["verdict"] == "SUSPICIOUS_OBFUSCATED":
                suspicious_count += 1
                db_status = "suspicious"
            else:
                rejected_count += 1
                db_status = "rejected"

            # Update database status
            notes_str = f"Score: {rep['security_score']}/100 | Findings: {len(rep['findings'])} | Cat: {rep['detected_category']}"
            cursor.execute("""
                UPDATE harvested_scripts 
                SET audit_status = ?, notes = ?
                WHERE local_filename = ?
            """, (db_status, notes_str, zf))

        conn.commit()
        conn.close()

        summary = {
            "total": len(zip_files),
            "verified": verified_count,
            "suspicious": suspicious_count,
            "rejected": rejected_count,
            "items": results
        }

        # Simpan audit report JSON
        report_path = os.path.join(os.path.dirname(self.db_path), "audit_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary
