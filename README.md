# 🎨 WoW Icon Tools

A professional batch processing toolkit for creating custom **World of Warcraft®** icon packs using reusable GIMP templates.

WoW Icon Tools automates the complete icon pipeline—from Blizzard BLP files to polished TGA icons—with a single command.

Designed for UI creators, addon authors, and anyone building large custom icon collections.

---

## Why WoW Icon Tools?

Creating thousands of custom icons by hand is incredibly time-consuming.

WoW Icon Tools was built to automate that process while remaining flexible enough for anyone to create and share their own icon styles.

Whether you're updating Blizzard's entire icon library or building a brand-new visual theme, WoW Icon Tools handles the repetitive work so you can focus on design.

---

# ✨ Features

- 🎮 Batch converts Blizzard BLP files to PNG
- 🖼 Automatically resizes icons to 128×128
- 🎨 Renders icons using reusable GIMP templates
- 📦 Exports directly to TGA
- 🔄 Resume Mode — automatically skips completed icons
- 📂 Automatic template discovery
- ✔ Template validation before rendering
- 🔍 Automatic GIMP detection
- 🖥 Clean professional console interface
- ⚡ Designed for processing 30,000+ icons

---

# 📸 Example Output

```text
==================================================
 WoW Icon Tools v1.1.0
==================================================

ℹ Preparing icon pipeline...

--------------------------------------------------
Rendering Icons
--------------------------------------------------

[1/31995] ✓ Saved: Ability_Fireball.tga
[2/31995] ✓ Saved: Ability_Frostbolt.tga
[3/31995] ⚠ Skipped: Ability_Heal.tga

==================================================
Build Complete
==================================================

Template.......... Eclipse
Rendered.......... 31995
Skipped........... 0
Failed............ 0

Elapsed Time...... 18m 22s

✓ Build completed successfully!

Thank you for using WoW Icon Tools!
```

---

# 🚀 Requirements

- Python 3.14+
- GIMP 3.x
- Pillow

---

# 🚀 Getting Started

## Step 1 — Download

On the GitHub page, click **Code → Download ZIP**.

Extract the ZIP file anywhere on your computer.

Example:

```
Documents
└── WoW Icon Tools
```

---

## Step 2 — Install Python

Download the latest version of Python from:

https://www.python.org/downloads/

> **Important:** During installation, make sure **"Add Python to PATH"** is checked.

---

## Step 3 — Install GIMP 3

Download and install GIMP 3:

https://www.gimp.org/downloads/

WoW Icon Tools will automatically detect your GIMP installation.

---

## Step 4 — Install Pillow

Open **PowerShell** inside the `Scripts` folder.

Run:

```powershell
pip install pillow
```

---

## Step 5 — Launch WoW Icon Tools

Inside the `Scripts` folder, run:

```powershell
python build_icon.py
```

The application will guide you through the rest.

---

## First Run

1. Place your Blizzard `.blp` files inside the **BLP** folder.
2. Run `build_icon.py`.
3. Select a template.
4. Sit back while WoW Icon Tools processes your icons.

Finished icons will appear inside the **ICONS** folder.
---

# ❓ New to Python?

Don't worry!

WoW Icon Tools only requires one Python package (`Pillow`) and a GIMP installation.

Once those are installed, you'll simply run:

```powershell
python build_icon.py
```

Everything else is handled automatically.

# ▶ How It Works

The entire build pipeline is automated.

```
Blizzard BLP Files
        │
        ▼
Convert to PNG
        │
        ▼
Resize Images
        │
        ▼
Select Template
        │
        ▼
Validate Template
        │
        ▼
Render Through GIMP
        │
        ▼
Export Finished Icons
```

If the build is interrupted, simply run it again.

Completed stages are reused when their SHA-256 fingerprints still match.

---

# 📁 Project Structure

```text
WoW Icon Tools

├── BLP/
├── PNG/
├── PNG_128x128_Resized/
├── ICONS/
├── Logs/

├── Templates/
│   └── Eclipse/
│       ├── Eclipse.xcf
│       ├── preview.png
│       └── template.json

├── Scripts/

├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## 🎨 Creating Your Own Templates

Templates are completely modular. Each template is stored in its own folder inside the `Templates` directory.

To add a custom template, create a new folder and give it a descriptive name.

Example:

```text
Templates/
├── Eclipse/
│   ├── Eclipse.xcf
│   ├── preview.png
│   └── template.json
│
└── Obsidian/
    ├── Obsidian.xcf
    ├── preview.png
    └── template.json
```

WoW Icon Tools automatically scans the `Templates` folder at startup and lists every valid template it finds.

No Python code changes are required when adding another template.

## Template Requirements

Each template folder must contain:

- A GIMP `.xcf` template file
- A file named exactly `template.json`
- An optional `preview.png` image

> **Important:** The `template.json` filename is required and must not be renamed.

The XCF file may use any filename, provided the same filename is entered in `template.json`.

For example:

```json
{
    "name": "Eclipse",
    "description": "Clean glossy ElvUI-style icons with dark edges, subtle glow, and reflective glare.",
    "author": "IHealDrunk",
    "version": "1.0.0",

    "template_file": "Eclipse.xcf",
    "preview": "preview.png",

    "replace_layer": "ICON",
    "icon_size": 128,
    "export_format": ".tga"
}
```

The `template.json` file defines:

- Template name
- Description
- Author
- Version
- GIMP template filename
- Preview image filename
- Replacement layer
- Icon size
- Export format

The XCF template must contain a layer matching the name entered under `replace_layer`.

For the example above, the XCF must contain a layer named:

```text
ICON
```

During rendering, WoW Icon Tools replaces that layer with each resized icon while preserving the remaining GIMP layers, blend modes, opacity settings, and layer order.

The optional `preview.png` should show what the finished template looks like.

## Version 1.1 — Released

- ✅ Complete batch processing pipeline
- ✅ BLP-to-PNG conversion
- ✅ Automatic 128×128 icon resizing
- ✅ GIMP-based rendering
- ✅ TGA export
- ✅ Resume Mode
- ✅ Modular template system
- ✅ Automatic template discovery
- ✅ Custom XCF filenames
- ✅ Template metadata
- ✅ Template validation
- ✅ Automatic GIMP detection
- ✅ Professional console interface
- ✅ Progress bar
- ✅ Warning when `ICONS` folder already contains files

## Future Improvements

- 

---

# 🤝 Contributing

Bug reports, feature requests, improvements, and new templates are always welcome.

If you'd like to improve WoW Icon Tools, feel free to open an Issue or submit a Pull Request.

---

# 📜 License

WoW Icon Tools is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

You are free to:

- Use the software
- Modify the source code
- Share the software
- Distribute modified versions

Any redistributed or modified version must also remain licensed under GPL-3.0 and include the corresponding source code.

See the included **LICENSE** file for the complete license text.

---

# 🙏 Acknowledgements

World of Warcraft® is a registered trademark of Blizzard Entertainment.

WoW Icon Tools is an independent, fan-made utility created for the World of Warcraft community.

This project is **not affiliated with, endorsed by, or sponsored by Blizzard Entertainment.**

## Version 1.3.0: Incremental Builds and Recovery

All three stages display percentage, files remaining, estimated time remaining
(labelled "How much longer this shit will be"),
completed work, reused outputs, and failures. Resizing also counts review files;
conversion counts cached bad BLPs. Estimates adapt to the current processing rate.

**Input sizes:** 64×64 BLPs use the original upscale/crop workflow. Native
128×128 BLPs pass through without resizing or cropping. Both produce 128×128
icons with the selected template. Other dimensions go to REVIEW. Previously
reviewed 128×128 files are picked up automatically.

**Your template-update workflow:** copy your existing Onyx, Eclipse, or other
finished set into `ICONS`, select its template, and choose Resume Build. Each
template has a separate completion history. New or changed source icons and
missing/damaged outputs are rendered; unchanged recorded icons bypass GIMP.
When existing files have no history for the selected template, choose **Use these
as the existing [template] set** to adopt them without rendering. This confirms
that they already use the selected template and match the current source icons.
Invalid or incorrectly sized files cannot be adopted. A changed source with an
existing record is rebuilt even if you choose adoption.

Editing a template applies the updated style to new or changed icons during
incremental updates. It does not automatically rebuild your whole existing set.
Choose **Start Over** for a full rebuild with the current template. Its existing
confirmation and `.gitkeep` protection remain. When rotating sets, keep your
upload copies outside `ICONS` and replace that folder with the next template's set.
Do not delete `Logs/build-state.json` if you want to retain all template histories.

**Faster rendering:** up to 32 icons share one GIMP session and loaded master
image; each render uses a fresh duplicate. Completed exports replace their
outputs atomically. The remaining members of a failed batch are retried
individually so one bad icon cannot block its peers.

**Controls:** press **P** to pause, then **R** to resume or **S** for Save & Exit.
**S** also works directly, and **Ctrl+C** requests a pause. Interactive key
controls require a Windows console. In a live GIMP batch, completed exports are
tracked individually; the small active batch may finish while paused or exiting.
No new batch is scheduled. Uncommitted temporary exports are discarded and
retried on recovery, while already published exports are reused.

**Checkpoint:** `Logs/build-state.json` holds SHA-256 records for conversion,
resizing, cached failures, and each template's finished icons. It is written
atomically, normally at most once every two seconds during processing, and
flushed at stage/batch boundaries and Save & Exit. Unexpected termination can
require a small amount of uncheckpointed work to be repeated. Old checkpoints
load without clearing your saved progress; matching old render records migrate
to the selected template's history.

**Skipping and validation:** unchanged good PNGs are reused after fingerprint
checks, without decoding their BLPs again. Existing PNGs/resized PNGs without
records are validated once and reused without rewriting when their pixels match.
New/modified BLPs and missing/damaged intermediates are regenerated. Paths and
extensions are compared case-insensitively, and nested paths are preserved.
Unchanged failed BLPs are skipped using their cached source hashes and retried
when they change. Output-write/permission failures are retried rather than cached
as bad BLPs. Failed conversion never feeds old PNGs into later stages.

BLP decoding supports Pillow palette/DXT formats and BLP2 raw BGRA (encoding 3).
Invalid or truncated files report a re-extraction error. Files for deleted or
now unsupported source dimensions remain in ICONS for manual cleanup. A corrupt
checkpoint stops with an explanation; preserve it and move it aside to rebuild.

Build helpers live in `Scripts/utils.py`, decoding/conversion in
`Scripts/blp_to_png.py`, and the shared status display in `Scripts/console.py`.
Temporary batch scripts/logs are removed after use.

Run fixture tests from the project root:

```powershell
python -m unittest discover -s Tests -v
```

The final summary reports cached bad BLPs and files needing review separately
from new failures. An unchanged cached bad file is skipped, not counted as a new
error. Its source still needs re-extraction if you want to include that icon.
