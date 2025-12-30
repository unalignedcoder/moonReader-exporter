<img width="538" height="476" alt="Asset 3" src="https://github.com/user-attachments/assets/bd4725c5-c451-4a95-ba6b-21468a078e51" />

# Moon+ Reader Exporter

Standalone Python tool to export highlights and notes from **Moon+ Reader** (Android) to your PC as clean, formatted HTML files.

This script **does not require Calibre** and works with or without **Root**. It uses [ADB](https://developer.android.com/tools/adb) (included).

## Features

This script extracts **notes** and **highlights** from Moon+ Reader books, producing them in clean, well formatted html files.

It reads the e-book files from your device to extract the text *surrounding* your highlights, giving **full context**.

<p><img width="631" height="223" alt="image" src="https://github.com/user-attachments/assets/a20aa09c-a143-4c2c-b704-93079a538aed" />
<br /><sup>Highlights are much more useful if saved in context.</sup></p>

It respects **the highlight colors** selected in MoonReader.
<p><img width="270" height="265" alt="image" src="https://github.com/user-attachments/assets/3db8179b-24a1-45f6-b3a0-da92ac225013" /><img height="265" alt="image" src="https://github.com/user-attachments/assets/ad42e023-d014-4d62-9726-908d6a43253c" />
<br /><sup>The original highlights in Moon+ Reader, and the exported HTML file.</sup></p>

Furthermore:

* If a book was moved after import (e.g., from Downloads to Books), the script automatically searches the library to find it.
* Tracks export history and only processes *new* highlights on subsequent runs, saving massive amounts of time.
* **Dual Mode:**
    * **Root Mode:** Directly pulls the live database from `/data/data/` on Android.
    * **Non-Root Mode:** Automatically finds and extracts Notes from Moon+ Reader backups.
* Works on Windows, macOS, and Linux.

## Prerequisites

1.  **Python 3.6+** installed on your computer.
2.  **USB Debugging** enabled on your Android device.
3.  **(Optional) Bundled ADB:** `adb.exe` (and its DLLs) can be found in the `/adb` folder next to the script. Otherwise, the script can use your system's ADB.

## Installation

1.  Grab the zip file from the [latest release](https://github.com/unalignedcoder/moonReader-exporter/releases). What you need are `mre.py`, `mre.json` and the `adb` folder as well, unless you already have adb in your PATH.
2.  Install the required Python library for HTML parsing:
    ```bash
    pip install beautifulsoup4
    ```

## Usage

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

9) Enjoy fantastically well formatted Highlights and Notes saved for you in the context in which they were first taken, for research or memory.

<p align=center>Why, thank you for asking!<br />👉 You can donate to my projects <a href="https://www.buymeacoffee.com/unalignedcoder" target="_blank" title="buymeacoffee.com">here</a>👈</p>
