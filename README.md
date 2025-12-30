<img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/e38c6c7e-45cc-484e-804b-80b497c8f6c2" /><img width="256" height="256" alt="Asset 1@2x" src="https://github.com/user-attachments/assets/83666882-a4a5-47ed-b2aa-eb71cd517d2d" />


# Moon+ Reader Exporter

Standalone Python tool to export highlights and notes from **Moon+ Reader** (Android) to your PC as clean, formatted HTML files.

This script **does not require Calibre**, works with or without **Root**, and bypasses common MTP connection issues by using ADB (included).

## 🚀 Features

This script extract **notes** and **highlights** from Moon+ Reader books, producing them in clean, well formatted html files.

It reads the e-book files from your device to extract the text *surrounding* your highlights, giving **full context**.

<p><img width="631" height="223" alt="image" src="https://github.com/user-attachments/assets/a20aa09c-a143-4c2c-b704-93079a538aed" />
<br /><sup>Highlights are much more useful if saved in context.</sup></p>

It respects **the highlight colors** selected in MoonReader.
<p><img width="270" height="265" alt="image" src="https://github.com/user-attachments/assets/3db8179b-24a1-45f6-b3a0-da92ac225013" /><img width="320" height="221" alt="image" src="https://github.com/user-attachments/assets/ad42e023-d014-4d62-9726-908d6a43253c" />
<br /><sup>The original highlights in Moon+ Reader, and the exported HTML file.</sup></p>

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
   <p><img width="450" height="221" alt="image" src="https://github.com/user-attachments/assets/6f2725ab-e63b-4c87-a5e0-3b079786335a" /></p>
   
   - Consider that paths can be relative (e.g. 'MoonReader_notes') or absolute (e.g. 'C:/Backups'). Under Windows, always use forward slashes `/`, or double back slashes `\\`;
   - Set `context_chars` to indicate the amount of characters preceding and following the highlighted quote, for context;
   - Set `disable_context` to `true` to skip book downloading/parsing entirely (significantly faster, but highlights and notes only);
   - Set `enable_logging` to `true` to save a detailed session log to the export folder;
   - Set `use_root` to `false` to force extraction from the Backup file. If `true`, on a rooted phone it reads the database directly from the `/data/data` Moonreader folder.

5) Connect the phone to the PC, and make sure [USB Debugging](https://www.embarcadero.com/starthere/xe5/mobdevsetup/android/en/enabling_usb_debugging_on_an_android_device.html) is enabled:   
   <p><img width="540" height="250" alt="image" src="https://github.com/user-attachments/assets/a70a6f03-5391-4066-8ebc-647de2329365" /></p>

7) Launch the script from your pc: `python mre.py`   
   <p><img width="924" height="271" alt="image" src="https://github.com/user-attachments/assets/b86766e5-c916-4ea4-9f69-fd438d13b4a2" /></p>

9) Enjoy fantastically well formatted Higlights and Notes saved for you in the context in which they were first taken, for research or memory.

<p align=center>Why, thank you for asking!<br />👉 You can donate to my projects <a href="https://www.buymeacoffee.com/unalignedcoder" target="_blank" title="buymeacoffee.com">here</a>👈</p>
