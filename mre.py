"""
.SYNOPSIS
    Moon+ Reader Exporter - Extract highlights and notes from Moon+ Reader app on Android devices.

.NOTES
    - Fixed inconsistencies with MoonReader highlight styles.
    - Improved Terminal output
    - Improved HTML rendering output
    - Many minor fixes and improvements.
"""
__version__ = "1.0.3"

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
import datetime
import warnings

# =========================================================
# CLASS: CONFIGURATION MANAGER
# Handles loading/saving 'mre.json' and resolving relative paths.
# =========================================================
class ConfigManager:
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.config_path = os.path.join(script_dir, "mre.json")
        
        # Calculate default relative paths for a portable setup
        binary_name = "adb.exe" if os.name == 'nt' else "adb"
        default_adb_rel = os.path.join("adb", binary_name)
        default_export_rel = os.path.join("MoonReader_notes")
        
        # Default settings dictionary, in case the json file is missing
        self.defaults = {
            "export_dir": default_export_rel,
            "manual_adb_path": default_adb_rel,
            "context_chars": 400,
            "disable_context": False,
            "enable_logging": True,
			"log_file": "mre.log",
            "use_root": True
        }
        self.settings = self.load()

    def load(self):
        """Loads config, stripping comments (lines starting with //) before parsing JSON."""
        if not os.path.exists(self.config_path): return self.create_default()
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = "\n".join([line for line in f if not line.strip().startswith("//")])
                loaded = json.loads(content)
                # Merge user config with defaults to ensure all keys exist
                for key, val in self.defaults.items():
                    if key not in loaded: loaded[key] = val
                return loaded
        except json.JSONDecodeError as e:
            print(f"\n[CRITICAL CONFIG ERROR] Could not parse 'mre.json'.")
            print(f"Error details: {e}")
            sys.exit(1)
        except Exception: return self.create_default()

    def create_default(self):
        """Creates a fresh config file with default settings."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.defaults, f, indent=4)
        return self.defaults

    def get(self, key):
        """Returns the raw value from the config."""
        return self.settings.get(key)

    def get_path(self, key):
        """
        Smart path resolver:
        1. Normalizes slashes for the OS (Windows vs Linux).
        2. Converts relative paths (e.g. "adb/adb.exe") to absolute paths based on script location.
        """
        val = self.settings.get(key)
        if not val: return None
        clean_val = val.replace("/", os.sep) if os.name == 'nt' else val
        if os.path.isabs(clean_val): return clean_val
        return os.path.abspath(os.path.join(self.script_dir, clean_val))

# =========================================================
# SETUP GLOBALS
# =========================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = ConfigManager(SCRIPT_DIR)
EXPORT_DIR = CONFIG.get_path("export_dir")
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")
HISTORY_FILE = os.path.join(EXPORT_DIR, "export_history.json") 
# Moon+ Reader Package IDs and Database filenames
MOON_PACKAGES = ["com.flyersoft.moonreaderp", "com.flyersoft.moonreader"]
DB_NAMES = ["mrbooks.db", "book_notes.db", "notes.db"]
BACKUP_DIR = "/sdcard/Books/MoonReader/Backup/"

# =========================================================
# CLASS: LOGGER
# Handles dual output to Console (Steady Line) and Text File (Detailed History).
# =========================================================
class Logger:
    def __init__(self, log_path, enabled):
        self.enabled = enabled
        self.log_file = log_path
        self.session_start = False
        
    def log(self, message, console=True, overwrite=False):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        
        # 1. Console Output Logic
        if console:
            # Get terminal width to ensure we fully wipe previous long lines
            width = shutil.get_terminal_size().columns - 1
            
            if overwrite:
                # Truncate if message is longer than screen width to prevent wrapping
                clean_msg = message
                if len(clean_msg) > width: 
                    clean_msg = clean_msg[:width-3] + "..."
                
                # \r moves to start. <{width} pads with spaces to the right.
                print(f"\r{clean_msg:<{width}}", end="", flush=True)
            else:
                # If we are printing a normal message (like an error), 
                # first WIPE the steady line so it doesn't look messy.
                print(f"\r{' ' * width}\r", end="") 
                print(message)
        
        # 2. File Output Logic
        if self.enabled and self.log_file:
            if not self.session_start:
                try:
                    log_dir = os.path.dirname(self.log_file)
                    if log_dir and not os.path.exists(log_dir): os.makedirs(log_dir)
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(f"\n\n=== SESSION START {datetime.datetime.now()} ===\n")
                    self.session_start = True
                except: pass
            
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} {message}\n")
            except: pass

# =========================================================
# CLASS: ADB ENGINE
# Wraps subprocess calls to ADB executable.
# =========================================================
class AdbEngine:
    def __init__(self, logger):
        self.logger = logger
        self.adb_exe = self._find_adb()
        if not self.adb_exe:
            self.logger.log("CRITICAL: ADB not found. Please check 'manual_adb_path' in mre.json.")
            sys.exit(1)
        self.file_cache = None

    def _find_adb(self):
        """Locates ADB: Checks Config -> Checks 'adb' subfolder -> Checks System PATH."""
        manual = CONFIG.get_path("manual_adb_path")
        if manual and os.path.exists(manual): return manual
        
        binary_name = "adb.exe" if os.name == 'nt' else "adb"
        bundled = os.path.join(SCRIPT_DIR, "adb", binary_name)
        if os.path.exists(bundled): return bundled
        return shutil.which("adb")

    def run(self, args):
        """Runs an ADB command and returns the result."""
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        try:
            return subprocess.run([self.adb_exe] + args, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)
        except Exception as e:
            self.logger.log(f"ADB Error: {e}", console=True)
            return None

    def check_root(self):
        """Checks if the device has root access via 'su'."""
        res = self.run(["shell", "su", "-c", "id"])
        return res and "uid=0(root)" in res.stdout

    def build_file_cache(self, moonreader_books):
        """Indexes all files in the books directory to find 'moved' books later."""
        if not moonreader_books: moonreader_books = "/sdcard/Books/"
        
        # Show "Indexing..." on console because it takes time, but overwrite it later
        self.logger.log(f"Indexing library files in {moonreader_books}...", overwrite=True)
        
        res = self.run(["shell", "find", moonreader_books, "-type", "f"])
        cache = {}
        if res and res.returncode == 0:
            for line in res.stdout.splitlines():
                path = line.strip()
                if path: cache[os.path.basename(path)] = path
        self.file_cache = cache
        
        # Log count to file only (User requested skip on console)
        self.logger.log(f"Indexed {len(cache)} books.", console=False)
        
        # Clean the "Indexing..." line from screen so main loop starts fresh
        self.logger.log("", overwrite=True)

    def find_file_cached(self, filename):
        """Returns full path of a book from cache if it was moved."""
        # Note: We now pre-build this in main(), but this check remains safe
        if self.file_cache is None: self.build_file_cache(CONFIG.get("moonreader_books"))
        return self.file_cache.get(filename)

# =========================================================
# CLASS: HISTORY MANAGER
# Tracks which highlights have already been exported to skip processing.
# =========================================================
class HistoryManager:
    def __init__(self):
        self.history = {}
        if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except: pass

    def should_process(self, title, latest_timestamp):
        """Returns True if the book has new highlights since last run."""
        return latest_timestamp > self.history.get(title, 0)

    def update(self, title, latest_timestamp):
        self.history[title] = latest_timestamp

    def save(self):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

# =========================================================
# CLASS: DATA EXTRACTOR
# Handles logic for pulling Databases (Root/Backup) and Files.
# =========================================================
class DataExtractor:
    def __init__(self, adb, logger):
        self.adb = adb
        self.logger = logger
        self.use_root_pref = CONFIG.get("use_root")
        # Determine effective root status based on preference AND availability
        self.is_rooted = adb.check_root() if self.use_root_pref else False
        
        if self.is_rooted: self.logger.log("INFO: Root access confirmed.")
        elif self.use_root_pref: self.logger.log("INFO: No root access detected. Using backup mode.")
        else: self.logger.log("INFO: Root mode disabled in config. Using backup mode.")

    def find_and_pull_db(self, local_dest):
        """Attempts to retrieve the Moon+ Reader database file."""
        # METHOD 1: Direct Root Access (preferred if rooted)
        if self.is_rooted:
            self.logger.log("INFO: Checking internal storage for DB...", overwrite=True)
            temp_remote = "/sdcard/moon_temp_pull.db"
            for pkg in MOON_PACKAGES:
                for db_name in DB_NAMES:
                    full_path = f"/data/data/{pkg}/databases/{db_name}"
                    # Check if DB exists
                    if self.adb.run(["shell", "su", "-c", f"'ls {full_path}'"]).returncode == 0:
                        self.logger.log(f"  -> Found live DB: {full_path}", console=False)
                        # Copy to SD card (public space) then pull
                        self.adb.run(["shell", "su", "-c", f"'cp {full_path} {temp_remote} && chmod 666 {temp_remote}'"])
                        self.adb.run(["pull", temp_remote, local_dest])
                        self.adb.run(["shell", "rm", temp_remote])
                        return True
        
        # METHOD 2: Backup File (.mrpro) Extraction (fallback)
        self.logger.log("INFO: Checking backup folder...", overwrite=True)
        res = self.adb.run(["shell", "ls", BACKUP_DIR])
        if res and res.returncode == 0:
            # Find the newest .mrpro file
            files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith('.mrpro')]
            if files:
                files.sort(reverse=True)
                latest = BACKUP_DIR + files[0]
                self.logger.log(f"  -> Pulling backup: {latest}")
                zip_path = local_dest + ".zip"
                # Pull zip, extract relevant DB file
                if self.adb.run(["pull", latest, zip_path]).returncode == 0:
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as z:
                            # .mrpro files contain .tag files which are the databases
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
# HELPER FUNCTIONS: TEXT & STYLING
# =========================================================
def normalize_text(text):
    """Collapses multiple spaces/newlines into single spaces."""
    return re.sub(r'\s+', ' ', text).strip()

def android_color_to_css(color_int):
    """Converts Android/Java integer color to CSS Hex string."""
    if color_int is None or color_int == 0: return None
    # Mask to 32-bit signed int
    val = color_int & 0xFFFFFFFF
    # Last 6 hex digits are the RGB color
    return f"#{val & 0xFFFFFF:06x}"

def generate_style_string(color_int, underline, strikethrough, bak):
    hex_color = android_color_to_css(color_int)
    styles = []
    
    # CASE 1: Background Highlight (All flags are 0)
    # This covers standard highlights where text is just colored/highlighted background
    if underline == 0 and strikethrough == 0 and (bak is None or bak == 0):
        bg = hex_color if hex_color else "#fff59d" # Default yellow
        styles.append(f"background-color: {bg}")
        styles.append("color: inherit") # Keep text color natural
        
    # CASE 2: Text Decorations (Squiggly, Underline, Strikethrough)
    else:
        decos = []
        deco_style = "solid" # Default line style
        
        # 'bak=1' indicates Squiggly (Wavy) Underline
        if bak == 1:
            decos.append("underline")
            deco_style = "wavy"
        
        # Standard Underline
        if underline == 1:
            decos.append("underline")
            
        # Strikethrough
        if strikethrough == 1:
            decos.append("line-through")
            
        # Remove duplicates (e.g. if both bak=1 and underline=1 add "underline")
        decos = list(set(decos))
        
        if decos:
            styles.append(f"text-decoration: {' '.join(decos)}")
            styles.append(f"text-decoration-style: {deco_style}")
            if hex_color:
                styles.append(f"text-decoration-color: {hex_color}")
                styles.append("text-decoration-thickness: 2px")
            styles.append("background-color: transparent")

    return "; ".join(styles)

def extract_context(book_path, highlight):
    """
    Opens the EPUB (zip), finds the highlight, and extracts surrounding text.
    """
    if not book_path or not os.path.exists(book_path): return None
    if book_path.lower().endswith('.pdf'): return None # PDF parsing not supported
    
    try:
        from bs4 import BeautifulSoup
        target = normalize_text(highlight)
        if not target: return None
        padding = CONFIG.get("context_chars")

        with zipfile.ZipFile(book_path, 'r') as z:
            for n in z.namelist():
                # Only check HTML-like files inside the EPUB
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
                            # We leave a placeholder to inject the styled span later
                            after = clean_content[idx+len(target):end]
                            return f"{'...' if start>0 else ''}{before} <span class='highlight-placeholder'>###MATCH###</span> {after}{'...' if end<len(clean_content) else ''}"
    except: pass
    return None

def safe_remove(path):
    """Retries file deletion to handle Windows file locking delays."""
    if not os.path.exists(path): return
    for i in range(3):
        try: os.remove(path); return
        except PermissionError: time.sleep(0.1)

# =========================================================
# MAIN EXECUTION FLOW
# =========================================================
def main():
    if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)
    
    # 1. Init Logging
    enable_log = CONFIG.get("enable_logging")
    log_path = CONFIG.get_path("log_file")
    logger = Logger(log_path, enable_log)
    
    logger.log(f"=== Moon+ Exporter = v{__version__} ===")
    
    # 2. Redirect Python/BS4 Warnings to Logger
    def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
        msg = f"WARNING: {category.__name__}: {message} ({filename}:{lineno})"
        logger.log(msg, console=False)
    
    warnings.showwarning = custom_warning_handler
    
    # 3. Init Modules
    adb = AdbEngine(logger)
    extractor = DataExtractor(adb, logger)
    history = HistoryManager()
    
    disable_context = CONFIG.get("disable_context")
    if disable_context:
        logger.log("INFO: Context extraction disabled via config.")
    
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    local_db = os.path.join(TEMP_DIR, "moon.db")
    
    # 4. Pull Database
    if not extractor.find_and_pull_db(local_db):
        logger.log("FAILURE: No database found.")
        return

    # 5. Read Database
    conn = sqlite3.connect(local_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(notes)")
    db_cols = [r[1] for r in cursor.fetchall()]
    has_author = "author" in db_cols
    has_style = "bak" in db_cols and "underline" in db_cols
    
    cols = ["book as title", "original", "note", "filename", "highlightColor", "time"]
    if has_author: cols.append("author")
    if has_style: cols.extend(["underline", "strikethrough", "bak"])
    
    query = f"SELECT {', '.join(cols)} FROM notes WHERE original IS NOT NULL AND original != '' ORDER BY time DESC"
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        logger.log(f"SQL Error: {e}"); conn.close(); return
    conn.close()
    
    logger.log(f"Found {len(rows)} highlights.")
    
    # 6. Pre-Index Files (NEW: Prevents interruption during loop)
    if not disable_context:
        adb.build_file_cache(CONFIG.get("moonreader_books"))
    
    # Group highlights by Book Title
    books = {}
    for r in rows:
        title = r['title']
        if title not in books: books[title] = []
        books[title].append(r)

    processed = 0
    skipped = 0
    used_filenames = set()

# 7. Process Books
    for title, highlights in books.items():
        # CHECK: Use [0] (Newest) because query is DESC.
        # This ensures we skip books that haven't changed since the last run.
        if not history.should_process(title, highlights[0]['time']):
            skipped += 1
            continue

        # Steady Console Line
        logger.log(f"Processing: {title}", overwrite=True)
        processed += 1
        
        author = highlights[0]['author'] if has_author and highlights[0]['author'] else "Unknown Author"
        
        # --- ROBUST PATH FINDING ---
        # Don't just trust the first highlight. Loop until we find a valid filename.
        # This fixes issues where one copy of the book in DB has no path.
        raw_path = None
        for h in highlights:
            if h['filename'] and h['filename'].strip():
                raw_path = h['filename']
                break
        
        has_book_file = False
        local_book_path = None # Initialize to safe default

        if raw_path:
            _, ext = os.path.splitext(raw_path)
            if not ext: ext = ".epub"
            local_book_path = os.path.join(TEMP_DIR, f"temp_book{ext}")
            
            safe_remove(local_book_path)
            
            # Pull Book File
            if not disable_context:
                adb_path = raw_path.replace("/storage/emulated/0/", "/sdcard/")
                pull_success = False
                
                # Attempt 1: Direct path
                if adb_path.startswith("/") and adb.run(["pull", adb_path, local_book_path]).returncode == 0:
                    pull_success = True
                
                # Attempt 2: Cached search (fallback if file moved)
                if not pull_success:
                    fname = os.path.basename(raw_path)
                    found = adb.find_file_cached(fname)
                    if found and adb.run(["pull", found, local_book_path]).returncode == 0:
                        pull_success = True
                
                if pull_success: has_book_file = True
        else:
            # If NO highlight has a filename, we skip context but still export text
            pass

        # Generate Output Filename
        safe_title = "".join(x for x in title if x.isalnum() or x in " _-").strip()
        candidate_name = f"{safe_title}.html"
        counter = 1
        while candidate_name in used_filenames:
            candidate_name = f"{safe_title} ({counter}).html"
            counter += 1
        used_filenames.add(candidate_name)
        html_path = os.path.join(EXPORT_DIR, candidate_name)
        
        # Write HTML
        try:
            # Prepare Timestamp
            # Use [0] (Latest) because query is DESC
            latest_ts_raw = highlights[0]['time']
            try:
                ts_seconds = int(latest_ts_raw) / 1000.0
                dt_obj = datetime.datetime.fromtimestamp(ts_seconds)
                formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = "Unknown Date"

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""<html><head><meta charset='utf-8'><title>{title}</title>
                <style>
                    body {{ font-family: "Georgia", "Times New Roman", serif; width: 95%; max-width: 850px; margin: 20px auto; line-height: 1.6; color: #333; background-color: #fdfdfd; }}
                    h1 {{ font-family: "Georgia", serif; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 5px; }}
                    .author {{ font-size: 0.6em; color: #777; font-weight: normal; margin-left: 10px; vertical-align: middle; }}
                    .last-update {{ font-family: sans-serif; font-size: 0.8em; color: #999; text-align: right; margin-bottom: 30px; }}
                    .card {{ margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                    .ctx {{ font-size: 1.1em; color: #444; }}
                    .note {{ font-weight: bold; margin-top: 10px; padding-left: 10px; border-left: 3px solid #ccc; color: #000; }}
                </style></head><body>""")
                
                f.write(f"<h1>{title}<span class='author'>by {author}</span></h1>")
                f.write(f"<div class='last-update'>Last highlight: {formatted_date}</div>")
                
                # REVERSE ITERATION: Print Oldest -> Newest (Reading Order)
                for h in reversed(highlights):
                    original = h['original']
                    note = h['note']
                    
                    style_str = ""
                    if has_style:
                        style_str = generate_style_string(h['highlightColor'], h['underline'], h['strikethrough'], int(h['bak']) if h['bak'] is not None else 0)
                    else:
                        style_str = "background-color: #fff59d; color: black;"

                    ctx_html = extract_context(local_book_path, original) if has_book_file else None
                    highlight_span = f"<span style='{style_str}; padding: 0 2px; border-radius: 2px;'>{original}</span>"
                    
                    f.write("<div class='card'>")
                    if ctx_html:
                        final_html = ctx_html.replace("<span class='highlight-placeholder'>###MATCH###</span>", highlight_span)
                        f.write(f"<div class='ctx'>{final_html}</div>")
                    else:
                        f.write(f"<div class='ctx'>{highlight_span}</div>")
                    if note: f.write(f"<div class='note'>{note}</div>")
                    f.write("</div>")
                f.write("</body></html>")
            
            # Update history using [0] (Latest)
            history.update(title, highlights[0]['time'])
            
        except Exception as e: 
            logger.log(f"[Error] {title}: {e}", console=True)
            
        if local_book_path: safe_remove(local_book_path)

    # Overwrite the last "Processing: [Book]" message
    if processed > 0:
        logger.log("-" * 40, overwrite=True)
    
    # Print a newline to "lock in" the last message so the footer doesn't overwrite it
    # print()

    try: shutil.rmtree(TEMP_DIR)
    except: pass
    history.save()
    
    #if processed == 0:
    logger.log("-" * 40)

    logger.log(f"Processed: {processed} books | Skipped: {skipped}")
    logger.log(f"Done! Exports at: {EXPORT_DIR}")
	
    if enable_log:
        log_name = os.path.basename(log_path)
        logger.log(f"See {log_name} for details.")

if __name__ == "__main__":
    main()
