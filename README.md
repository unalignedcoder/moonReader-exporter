<img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/e38c6c7e-45cc-484e-804b-80b497c8f6c2" /><img width="256" height="256" alt="Asset 1@2x" src="https://github.com/user-attachments/assets/83666882-a4a5-47ed-b2aa-eb71cd517d2d" />


# Moon+ Reader Exporter (Standalone)

Standalone Python tool to export highlights and notes from **Moon+ Reader** (Android) to your PC as clean, formatted HTML files.

This script **does not require Calibre**, works with or without **Root**, and bypasses common MTP connection issues by using ADB (included).

## 🚀 Features

This script extract **notes** and **highlights** from Moon+ Reader books, producing them in clean, well formatted html files.

It reads the e-book files from your device to extract the text *surrounding* your highlights, giving **full context**.

It respects **the highlight colors** selected in MoonReader.

<img width="1210" height="211" alt="image" src="https://github.com/user-attachments/assets/2f4172ba-92f2-46ba-abba-b0b3c17136c1" />

Furthermore:

* **ADB**: It uses ADB to directly access Moon+ Reader backups and databases, bypassing MTP filter issues.
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

## ⚙️ Usage

1) If your phone is rooted, you can jump to step 3;
2) Create a Backup from within Moon+ Reader (Settings > Backup.) Make sure it is saved somewhere within the Moon+ Reader `/Books` subfolders;
3) If needed, edit options in the `mre.json` configuration file:

   <img width="450" height="221" alt="image" src="https://github.com/user-attachments/assets/6f2725ab-e63b-4c87-a5e0-3b079786335a" />
   
   - Consider that paths can be relative (e.g. 'MoonReader_notes') or absolute (e.g. 'C:/Backups'). Under Windows, always use forward slashes `/`, or double back slashes `\\`;
   - Set `context_chars` to indicate the amount of characters preceding and following the highlighted quote, for context;
   - Set `disable_context` to `true` to skip book downloading/parsing entirely (significantly faster, but highlights and notes only);
   - Set `enable_logging` to `true` to save a detailed session log to the export folder;
   - Set `use_root` to `false` to force extraction from the Backup file. If `true`, on a rooted phone it reads the database directly from the `/data/data` Moonreader folder.

5) Connect the phone to the PC, and make sure [USB Debugging](https://www.embarcadero.com/starthere/xe5/mobdevsetup/android/en/enabling_usb_debugging_on_an_android_device.html) is enabled:
   <img width="540" height="250" alt="image" src="https://github.com/user-attachments/assets/a70a6f03-5391-4066-8ebc-647de2329365" />

6) Launch the script from your pc: `python mre.py`
   <img width="927" height="233" alt="image" src="https://github.com/user-attachments/assets/76a4bbd0-e54a-44b2-93a0-1ba721cdb4af" />

7) Enjoy fantastically well formatted Higlights and Notes saved for you in the context in which they were first taken, for research or memory.

