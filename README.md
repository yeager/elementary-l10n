# elementary-l10n

Translation status viewer for [elementary OS](https://elementary.io) components.

![GTK4 + Adwaita](https://img.shields.io/badge/GTK4-Adwaita-blue)
![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green)

## Features

- 📊 Fetches live translation status from [l10n.elementaryos.org](https://l10n.elementaryos.org/projects/)
- 🎨 Color-coded progress bars (red → yellow → green)
- 🌍 Language selector with system language auto-detection
- 🔀 Sort by most/least translated
- 🔗 Click any component to open it on Weblate
- ℹ️ Info dialog explaining how easy it is to contribute translations

## Screenshot

*GTK4/Adwaita app showing translation completion per component*

## Requirements

- Python 3.10+
- GTK 4
- libadwaita 1.x
- PyGObject

### Install dependencies

**elementary OS / Ubuntu:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-requests
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-requests
```

## Installation

```bash
pip install .
```

Or run directly:
```bash
python -m elementary_l10n.app
```

## Usage

```bash
elementary-l10n
```

The app will auto-detect your system language and show translation progress for all elementary OS components. Use the dropdown to switch languages, click any row to open it on Weblate.

## Contributing

Contributions welcome! This project uses:

- **Python** with **GTK4** and **libadwaita** via PyGObject
- **Weblate API** for fetching translation data

## Help Translate elementary OS!

You don't need to be a developer to contribute to elementary OS. Visit [l10n.elementaryos.org](https://l10n.elementaryos.org/), create an account, pick your language, and start translating!

## License

GPL-3.0-or-later — see [COPYING](COPYING) for details.

## Author

Daniel Nylander <daniel@danielnylander.se>
