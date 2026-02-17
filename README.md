# Translation Status

## Screenshot

![elementary L10n](screenshots/main.png)

A GTK4/Adwaita application for viewing elementary OS translation progress via Weblate.

![Screenshot](data/screenshots/screenshot-01.png)

## Features

- Fetches live translation status from a Weblate instance
- Color-coded progress bars (red → yellow → green)
- Language selector with system language auto-detection
- Sort by most/least translated
- Click any component to open it on Weblate
- Info dialog explaining how to contribute translations

## Installation

### Debian/Ubuntu

```bash
# Add repository
curl -fsSL https://yeager.github.io/debian-repo/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/yeager-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/yeager-archive-keyring.gpg] https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager.list
sudo apt update
sudo apt install elementary-l10n
```

### Fedora/RHEL

```bash
sudo dnf config-manager --add-repo https://yeager.github.io/rpm-repo/yeager.repo
sudo dnf install elementary-l10n
```

### From source

```bash
pip install .
elementary-l10n
```

## 🌍 Contributing Translations

This app is translated via Transifex. Help translate it into your language!

**[→ Translate on Transifex](https://app.transifex.com/danielnylander/elementary-l10n/)**

Currently supported: Swedish (sv). More languages welcome!

### For Translators
1. Create a free account at [Transifex](https://www.transifex.com)
2. Join the [danielnylander](https://app.transifex.com/danielnylander/) organization
3. Start translating!

Translations are automatically synced via GitHub Actions.

## License

GPL-3.0-or-later — Daniel Nylander <daniel@danielnylander.se>
