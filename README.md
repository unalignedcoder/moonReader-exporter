<img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/e38c6c7e-45cc-484e-804b-80b497c8f6c2" /><img width="256" height="256" alt="Asset 1@2x" src="https://github.com/user-attachments/assets/83666882-a4a5-47ed-b2aa-eb71cd517d2d" />


# Moon+ Reader Exporter (Standalone)

Standalone Python tool to export highlights and notes from **Moon+ Reader** (Android) to your PC as clean, formatted HTML files.

This script **does not require Calibre**, works with or without **Root**, and bypasses common MTP connection issues by using ADB (included).

## 🚀 Features

This script uses ADB to directly access Moon+ Reader backups and databases, bypassing MTP filter issues.

It extract **notes** and **highlights** from books, producing them in clean, well formatted html files.

It pulls the e-book file from your device to extract the text *surrounding* your highlight, giving full context.

It respects the highlight colors selected in MoonReader.

Furthermore:

* **Smart "Lost Book" Recovery:** If a book was moved after import (e.g., from Downloads to Books), the script automatically searches the library to find it.
* **Incremental Exports:** Tracks export history and only processes *new* highlights on subsequent runs, saving massive amounts of time.
* **Dual Mode:**
    * **Root Mode:** Directly pulls the live database from `/data/data/` on Android.
    * **Non-Root Mode:** Automatically finds and extracts `.mrpro` backups.
* **Cross-Platform:** Works on Windows, macOS, and Linux.
* **Configurable:** Auto-generates a JSON config file to tweak paths and settings.

## 📋 Prerequisites

1.  **Python 3.6+** installed on your computer.
2.  **USB Debugging** enabled on your Android device.
3.  **(Optional) Bundled ADB:** `adb.exe` (and its DLLs) can be found in the `/adb` folder next to the script. Otherwise, the script can use your system's ADB.

## 📦 Installation

1.  Clone or download this repository.
2.  Install the required Python library for HTML parsing:
    ```bash
    pip install beautifulsoup4
    ```
3.  Connect your Android phone via USB.

## ⚙️ Configuration

Run the script once to generate the default configuration file: `mre.json`.

```json
{
    "use_root": true,
    "export_dir": ".../MoonReader_notes",
    "manual_adb_path": ".../adb/adb.exe",
    "context_chars": 400,
    "moonreader_books": "/sdcard/Books/"
}
