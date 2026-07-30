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
 WoW Icon Tools v1.0.0
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

Existing icons are automatically skipped.

---

# 📁 Project Structure

```
WoW Icon Tools

├── BLP/
├── PNG/
├── PNG_128x128_Resized/
├── ICONS/

├── Templates/
│   └── Eclipse/

├── Scripts/

├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

# 🎨 Creating Your Own Templates

Templates are completely modular.

Simply create a new folder inside the **Templates** directory.

Example:

```
Templates/

    Eclipse/
        Master GIMP Template.xcf
        template.json
        preview.png
```

Each template defines:

- Name
- Description
- Author
- Version
- Replacement layer
- Export format
- Icon size

WoW Icon Tools automatically discovers new templates at startup.

No code changes are required.

---

# 🛣 Roadmap

## Version 1.0

- ✅ Complete batch processing pipeline
- ✅ Resume mode
- ✅ Modular template system
- ✅ Automatic template discovery
- ✅ Template validation
- ✅ Automatic GIMP detection
- ✅ Professional console interface

## Planned for Version 1.1

- 🖼 Template preview images
- ⚙ Configuration file
- 📊 Progress bar
- 🔍 Verbose mode
- 📦 Additional export formats

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