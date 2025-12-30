"""
.SYNOPSIS
Moon+ Reader Exporter - Extract highlights and notes from Moon+ Reader app on Android devices.

.NOTES
- Fixed the path handling issue.
- Improved config handling with a spearate json file
- Initial commit
"""
__version__ = "1.0.2"

import os
import sys
import shutil
import sqlite3
import zipfile
import subprocess
import re
import time
import json
import platform

# =========================================================
# CONFIGURATION MANAGER
# =========================================================
class ConfigManager:
    def __init__(self, script_dir):
        self.config_path = os.path.join(script_dir, "mre.json")
        
        # Calculate the absolute path to the bundled ADB for the default config
        binary_name = "adb.exe" if os.name == 'nt' else "adb"
        default_adb_path = os.path.join(script_dir, "adb", binary_name)
        
        self.defaults = {
            "export_dir": os.path.join(script_dir, "MoonReader_notes"),
            "manual_adb_path": default_adb_path,
            "context_chars": 400,
            "moonreader_books": "/sdcard/Books/",
            "_comment": "use_root: true to attempt root access; false to always use backup method",
            "use_root": False
        }
        self.settings = self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            return self.create_default()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge loaded config with defaults to ensure all keys exist
                for key, val in self.defaults.items():
                    if key not in loaded:
                        loaded[key] = val
                return loaded
        except:
            return self.create_default()

    def create_default(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.defaults, f, indent=4)
        print(f"Created new config file at: {self.config_path}")
        return self.defaults

    def get(self, key):
        return self.settings.get(key)

# =========================================================
# SETUP GLOBAL PATHS
# =========================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = ConfigManager(SCRIPT_DIR)

EXPORT_DIR = CONFIG.get("export_dir")
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")
HISTORY_FILE = os.path.join(EXPORT_DIR, "export_history.json") 

MOON_PACKAGES = ["com.flyersoft.moonreaderp", "com.flyersoft.moonreader"]
DB_NAMES = ["mrbooks.db", "book_notes.db", "notes.db"]
BACKUP_DIR = "/sdcard/Books/MoonReader/Backup/"

# =========================================================
# ADB ENGINE
# =========================================================
class AdbEngine:
    def __init__(self):
        self.adb_exe = self._find_adb()
        if not self.adb_exe:
            print("CRITICAL: ADB not found. Please install platform-tools or set path in mre.json")
            sys.exit(1)
        self.file_cache = None

    def _find_adb(self):
        # 1. Configured Path (Default now points to bundled)
        manual = CONFIG.get("manual_adb_path")
        if manual and os.path.exists(manual): return manual
        
        # 2. Bundled Fallback (Just in case config is weird)
        binary_name = "adb.exe" if os.name == 'nt' else "adb"
        bundled = os.path.join(SCRIPT_DIR, "adb", binary_name)
        if os.path.exists(bundled): return bundled
        
        # 3. System Path
        return shutil.which("adb")

    def run(self, args):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            return subprocess.run([self.adb_exe] + args, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)
        except Exception as e:
            print(f"ADB Error: {e}")
            return None

    def check_root(self):
        res = self.run(["shell", "su", "-c", "id"])
        return res and "uid=0(root)" in res.stdout

    def build_file_cache(self, moonreader_books):
        print(f"Indexing library files in {moonreader_books}...")
        cmd = ["shell", "find", moonreader_books, "-type", "f"]
        res = self.run(cmd)
        cache = {}
        if res and res.returncode == 0:
            lines = res.stdout.splitlines()
            for line in lines:
                path = line.strip()
                if path:
                    fname = os.path.basename(path)
                    cache[fname] = path
        self.file_cache = cache
        print(f"Indexed {len(cache)} books.")

    def find_file_cached(self, filename):
        if self.file_cache is None:
            self.build_file_cache(CONFIG.get("moonreader_books"))
        return self.file_cache.get(filename)

# =========================================================
# HISTORY TRACKER
# =========================================================
class HistoryManager:
    def __init__(self):
        self.history = {}
        if not os.path.exists(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except: pass

    def should_process(self, title, latest_timestamp):
        last_run_time = self.history.get(title, 0)
        return latest_timestamp > last_run_time

    def update(self, title, latest_timestamp):
        self.history[title] = latest_timestamp

    def save(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

# =========================================================
# DATA EXTRACTION
# =========================================================
class DataExtractor:
    def __init__(self, adb):
        self.adb = adb
        
        # Check config preference
        self.use_root_pref = CONFIG.get("use_root")
        
        if self.use_root_pref:
            self.is_rooted = adb.check_root()
        else:
            self.is_rooted = False

        if self.is_rooted: 
            print("INFO: Root access confirmed.")
        elif self.use_root_pref: 
            print("INFO: No root access detected. Using backup mode.")
        else:
            print("INFO: Root mode disabled in config. Using backup mode.")

    def find_and_pull_db(self, local_dest):
        # 1. ROOT METHOD (Only if configured AND available)
        if self.is_rooted:
            print("INFO: Checking internal storage for DB...")
            temp_remote = "/sdcard/moon_temp_pull.db"
            for pkg in MOON_PACKAGES:
                for db_name in DB_NAMES:
                    full_path = f"/data/data/{pkg}/databases/{db_name}"
                    if self.adb.run(["shell", "su", "-c", f"'ls {full_path}'"]).returncode == 0:
                        print(f"  -> Found live DB: {full_path}")
                        self.adb.run(["shell", "su", "-c", f"'cp {full_path} {temp_remote} && chmod 666 {temp_remote}'"])
                        self.adb.run(["pull", temp_remote, local_dest])
                        self.adb.run(["shell", "rm", temp_remote])
                        return True
        
        # 2. BACKUP METHOD (Fallback or Default if root disabled)
        print("INFO: Checking backup folder...")
        res = self.adb.run(["shell", "ls", BACKUP_DIR])
        if res and res.returncode == 0:
            files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith('.mrpro')]
            if files:
                files.sort(reverse=True)
                latest = BACKUP_DIR + files[0]
                print(f"  -> Pulling backup: {latest}")
                zip_path = local_dest + ".zip"
                if self.adb.run(["pull", latest, zip_path]).returncode == 0:
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as z:
                            tags = [n for n in z.namelist() if n.endswith('.tag')]
                            if tags:
                                tags.sort(key=lambda x: z.getinfo(x).file_size, reverse=True)
                                with open(local_dest, "wb") as f:
                                    f.write(z.read(tags[0]))
                                os.remove(zip_path)
                                return True
                    except: pass
                    if os.path.exists(zip_path): os.remove(zip_path)
        return False

# =========================================================
# CONTEXT ENGINE
# =========================================================
def normalize_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_context(book_path, highlight):
    if not book_path or not os.path.exists(book_path): return None
    if book_path.lower().endswith('.pdf'): return None
    
    try:
        from bs4 import BeautifulSoup
        target = normalize_text(highlight)
        if not target: return None
        
        padding = CONFIG.get("context_chars")

        with zipfile.ZipFile(book_path, 'r') as z:
            for n in z.namelist():
                if n.lower().endswith(('html', 'htm', 'xml', 'xhtml')):
                    raw_content = z.read(n).decode('utf-8', errors='ignore')
                    if highlight in raw_content:
                        soup = BeautifulSoup(raw_content, 'html.parser')
                        text_content = soup.get_text(separator=' ')
                        clean_content = normalize_text(text_content)
                        
                        idx = clean_content.find(target)
                        if idx != -1:
                            start = max(0, idx - padding)
                            end = min(len(clean_content), idx + len(target) + padding)
                            
                            before = clean_content[start:idx]
                            match = clean_content[idx:idx+len(target)]
                            after = clean_content[idx+len(target):end]
                            
                            prefix = "..." if start > 0 else ""
                            suffix = "..." if end < len(clean_content) else ""
                            return f"{prefix}{before} <span class='highlight-inline'>{match}</span> {after}{suffix}"
    except: pass
    return None

def safe_remove(path):
    if not os.path.exists(path): return
    for i in range(3):
        try:
            os.remove(path)
            return
        except PermissionError:
            time.sleep(0.1)
    print(f"  [Warn] Could not delete temp file: {path}")

# =========================================================
# MAIN
# =========================================================
def main():
    print("--- Moon+ Exporter (Final) ---")
    adb = AdbEngine()
    extractor = DataExtractor(adb)
    history = HistoryManager()
    
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    local_db = os.path.join(TEMP_DIR, "moon.db")
    
    if not extractor.find_and_pull_db(local_db):
        print("FAILURE: No database found.")
        return

    conn = sqlite3.connect(local_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(notes)")
    cols = [r[1] for r in cursor.fetchall()]
    has_author = "author" in cols
    
    query = "SELECT book as title, original, note, filename, highlightColor, time"
    if has_author: query += ", author"
    query += " FROM notes WHERE original IS NOT NULL AND original != '' ORDER BY time DESC"
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"SQL Error: {e}"); conn.close(); return
    conn.close()
    
    print(f"SUCCESS: Found {len(rows)} total highlights.")
    
    books = {}
    for r in rows:
        title = r['title']
        if title not in books: books[title] = []
        books[title].append(r)

    processed_count = 0
    skipped_count = 0

    for title, highlights in books.items():
        latest_ts = highlights[0]['time']
        
        if not history.should_process(title, latest_ts):
            skipped_count += 1
            continue

        print(f"Processing: {title}")
        processed_count += 1
        
        author = "Unknown Author"
        if has_author and highlights[0]['author']:
            author = highlights[0]['author']
            
        raw_path = highlights[0]['filename']
        has_book_file = False
        _, ext = os.path.splitext(raw_path)
        if not ext: ext = ".epub"
        local_book_path = os.path.join(TEMP_DIR, f"temp_book{ext}")
        
        safe_remove(local_book_path)
        
        if raw_path:
            adb_path = raw_path.replace("/storage/emulated/0/", "/sdcard/")
            pull_success = False
            
            if adb_path.startswith("/") and adb.run(["pull", adb_path, local_book_path]).returncode == 0:
                pull_success = True
            
            if not pull_success:
                filename = os.path.basename(raw_path)
                found_path = adb.find_file_cached(filename)
                if found_path and adb.run(["pull", found_path, local_book_path]).returncode == 0:
                    pull_success = True
            
            if pull_success:
                has_book_file = True

        safe_title = "".join(x for x in title if x.isalnum() or x in " _-").strip()
        html_path = os.path.join(EXPORT_DIR, f"{safe_title}.html")
        
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""<html><head><meta charset='utf-8'><title>{title}</title>
                <style>
                    body {{ font-family: "Georgia", "Times New Roman", serif; max-width: 800px; margin: 40px auto; line-height: 1.6; color: #333; background-color: #fdfdfd; }}
                    h1 {{ font-family: "Georgia", serif; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                    h2 {{ font-family: "Georgia", serif; font-size: 1.1em; color: #666; font-weight: normal; margin-top: -10px; }}
                    .card {{ margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                    .ctx {{ font-size: 1.1em; color: #444; }}
                    .highlight-inline {{ background-color: #fff59d; border-radius: 2px; padding: 0 2px; }}
                    .orphan-highlight {{ background-color: #fff59d; padding: 5px; display: inline-block; }}
                    .note {{ font-weight: bold; margin-top: 10px; padding-left: 10px; border-left: 3px solid #ccc; color: #000; }}
                </style></head><body>""")
                
                f.write(f"<h1>{title}</h1>")
                f.write(f"<h2>{author}</h2>")
                
                for h in highlights:
                    original = h['original']
                    note = h['note']
                    full_context_html = None
                    
                    if has_book_file:
                        full_context_html = extract_context(local_book_path, original)
                    
                    f.write("<div class='card'>")
                    if full_context_html:
                        f.write(f"<div class='ctx'>{full_context_html}</div>")
                    else:
                        f.write(f"<div class='ctx orphan-highlight'>{original}</div>")
                    
                    if note: f.write(f"<div class='note'>{note}</div>")
                    f.write("</div>")
                
                f.write("</body></html>")
            
            history.update(title, latest_ts)

        except Exception as e:
            print(f"  [Error] Failed to write HTML for {title}: {e}")
            
        safe_remove(local_book_path)

    try: shutil.rmtree(TEMP_DIR)
    except: pass
    
    history.save()
    
    print("-" * 40)
    print(f"Processed: {processed_count}")
    print(f"Skipped:   {skipped_count}")
    print(f"Done! Exports at: {EXPORT_DIR}")

if __name__ == "__main__":
    main()