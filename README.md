# Translation Status

Translation status viewer for Weblate-hosted projects.

![GTK4 + Adwaita](https://img.shields.io/badge/GTK4-Adwaita-blue)
![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green)

## Features

- 📊 Fetches live translation status from a Weblate instance
- 🎨 Color-coded progress bars (red → yellow → green)
- 🌍 Language selector with system language auto-detection
- 🔀 Sort by most/least translated
- 🔗 Click any component to open it on Weblate
- ℹ️ Info dialog explaining how to contribute translations

## Screenshot

*GTK4/Adwaita app showing translation completion per component*

## Requirements

- Python 3.10+
- GTK 4
- libadwaita 1.x
- PyGObject

### Install dependencies (Debian/Ubuntu)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-requests
```

## Installation

```bash
pip install .
```

Or run directly:

```bash
python -m elementary_l10n.app
```

## Flatpak

```bash
flatpak-builder --user --install build se.danielnylander.TranslationStatus.yml
flatpak run se.danielnylander.TranslationStatus
```

## Usage

```bash
elementary-l10n
```

The app auto-detects your system language and shows translation progress for all components. Use the dropdown to switch languages, click any row to open it on Weblate.

## License

GPL-3.0-or-later — see [COPYING](COPYING) for details.

## Author

Daniel Nylander <daniel@danielnylander.se>
