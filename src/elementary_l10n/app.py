"""Translation Status - GTK4/Adwaita Weblate translation viewer."""

import csv
import gettext
import json
import locale
import os
import sys
import webbrowser

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
# Optional desktop notifications
try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify as _Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False
from gi.repository import Gtk, Adw, Gio, GLib, Gdk, Pango  # noqa: E402

from . import weblate  # noqa: E402

# i18n setup
LOCALEDIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'po', 'locale')
if not os.path.isdir(LOCALEDIR):
    LOCALEDIR = '/usr/share/locale'
gettext.bindtextdomain('elementary-l10n', LOCALEDIR)
gettext.textdomain('elementary-l10n')
_ = gettext.gettext

# Common languages on Weblate
LANGUAGES = [
    ("aa", "Afar"), ("af", "Afrikaans"), ("am", "Amharic"), ("an", "Aragonese"),
    ("ar", "Arabic"), ("as", "Assamese"), ("ast", "Asturian"), ("az", "Azerbaijani"),
    ("be", "Belarusian"), ("bg", "Bulgarian"), ("bn", "Bengali"), ("br", "Breton"),
    ("bs", "Bosnian"), ("ca", "Catalan"), ("ckb", "Central Kurdish"),
    ("cs", "Czech"), ("cy", "Welsh"), ("da", "Danish"), ("de", "German"),
    ("el", "Greek"), ("en_AU", "English (Australia)"), ("en_GB", "English (UK)"),
    ("eo", "Esperanto"), ("es", "Spanish"), ("et", "Estonian"), ("eu", "Basque"),
    ("fa", "Persian"), ("fi", "Finnish"), ("fil", "Filipino"), ("fo", "Faroese"),
    ("fr", "French"), ("fy", "Western Frisian"), ("ga", "Irish"),
    ("gd", "Scottish Gaelic"), ("gl", "Galician"), ("gu", "Gujarati"),
    ("he", "Hebrew"), ("hi", "Hindi"), ("hr", "Croatian"), ("hu", "Hungarian"),
    ("hy", "Armenian"), ("id", "Indonesian"), ("is", "Icelandic"), ("it", "Italian"),
    ("ja", "Japanese"), ("ka", "Georgian"), ("kk", "Kazakh"), ("km", "Khmer"),
    ("kn", "Kannada"), ("ko", "Korean"), ("ku", "Kurdish"), ("ky", "Kyrgyz"),
    ("lb", "Luxembourgish"), ("lo", "Lao"), ("lt", "Lithuanian"), ("lv", "Latvian"),
    ("mg", "Malagasy"), ("mk", "Macedonian"), ("ml", "Malayalam"),
    ("mn", "Mongolian"), ("mr", "Marathi"), ("ms", "Malay"), ("mt", "Maltese"),
    ("my", "Burmese"), ("nb_NO", "Norwegian Bokmål"), ("ne", "Nepali"),
    ("nl", "Dutch"), ("nn", "Norwegian Nynorsk"), ("oc", "Occitan"),
    ("or", "Odia"), ("pa", "Punjabi"), ("pl", "Polish"),
    ("pt", "Portuguese"), ("pt_BR", "Portuguese (Brazil)"),
    ("ro", "Romanian"), ("ru", "Russian"), ("rw", "Kinyarwanda"),
    ("si", "Sinhala"), ("sk", "Slovak"), ("sl", "Slovenian"), ("sq", "Albanian"),
    ("sr", "Serbian"), ("sv", "Swedish"), ("sw", "Swahili"), ("ta", "Tamil"),
    ("te", "Telugu"), ("tg", "Tajik"), ("th", "Thai"), ("tk", "Turkmen"),
    ("tl", "Tagalog"), ("tr", "Turkish"), ("ug", "Uyghur"), ("uk", "Ukrainian"),
    ("ur", "Urdu"), ("uz", "Uzbek"), ("vi", "Vietnamese"),
    ("zh_CN", "Chinese (Simplified)"), ("zh_TW", "Chinese (Traditional)"),
    ("zu", "Zulu"),
]


def get_system_language() -> str:
    """Detect system language code."""
    try:
        loc = locale.getlocale()[0]  # e.g. 'sv_SE'
        if loc:
            for code, _ in LANGUAGES:
                if code == loc:
                    return code
            lang = loc.split("_")[0]
            for code, _ in LANGUAGES:
                if code == lang:
                    return code
    except Exception:
        pass
    return "sv"


def pct_to_color(pct: float) -> Gdk.RGBA:
    """Map 0-100% to red→yellow→green."""
    rgba = Gdk.RGBA()
    if pct < 50:
        r, g = 0.9, 0.2 + (pct / 50) * 0.7
    else:
        r, g = 0.9 - ((pct - 50) / 50) * 0.7, 0.9
    rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, 0.2, 1.0
    return rgba



import json as _json
import platform as _platform
from pathlib import Path as _Path

_NOTIFY_APP = "elementary-l10n"


def _notify_config_path():
    return _Path(GLib.get_user_config_dir()) / _NOTIFY_APP / "notifications.json"


def _load_notify_config():
    try:
        return _json.loads(_notify_config_path().read_text())
    except Exception:
        return {"enabled": False}


def _save_notify_config(config):
    p = _notify_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps(config))


def _send_notification(summary, body="", icon="dialog-information"):
    if HAS_NOTIFY and _load_notify_config().get("enabled"):
        try:
            n = _Notify.Notification.new(summary, body, icon)
            n.show()
        except Exception:
            pass


def _get_system_info():
    return "\n".join([
        f"App: Translation Status",
        f"Version: {"0.2.1"}",
        f"GTK: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
        f"Adw: {Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}",
        f"Python: {_platform.python_version()}",
        f"OS: {_platform.system()} {_platform.release()} ({_platform.machine()})",
    ])


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=_("Translation Status"),
                         default_width=900, default_height=700)

        self._data = []
        self._sort_ascending = True
        self._current_lang = get_system_language()

        # Header bar
        header = Adw.HeaderBar()

        # Language dropdown
        lang_model = Gtk.StringList()
        self._lang_codes = []
        selected_idx = 0
        for i, (code, name) in enumerate(LANGUAGES):
            lang_model.append(f"{name} ({code})")
            self._lang_codes.append(code)
            if code == self._current_lang:
                selected_idx = i

        self._lang_dropdown = Gtk.DropDown(model=lang_model, selected=selected_idx)
        self._lang_dropdown.set_tooltip_text(_("Select language"))
        self._lang_dropdown.connect("notify::selected", self._on_lang_changed)
        header.pack_start(self._lang_dropdown)

        # Status filter dropdown
        filter_model = Gtk.StringList()
        self._filter_options = [
            ("all", _("All")),
            ("complete", _("Fully translated (100%)")),
            ("partial", _("Partially translated (1–99%)")),
            ("untranslated", _("Untranslated (0%)")),
        ]
        for _key, label in self._filter_options:
            filter_model.append(label)
        self._filter_dropdown = Gtk.DropDown(model=filter_model, selected=0)
        self._filter_dropdown.set_tooltip_text(_("Filter by status"))
        self._filter_dropdown.connect("notify::selected", self._on_filter_changed)
        header.pack_start(self._filter_dropdown)

        # Sort button
        sort_btn = Gtk.Button(icon_name="view-sort-descending-symbolic",
                              tooltip_text=_("Toggle sort order"))
        sort_btn.connect("clicked", self._on_sort_clicked)
        header.pack_start(sort_btn)

        # Export button
        export_btn = Gtk.Button(icon_name="document-save-symbolic",
                                tooltip_text=_("Export data"))
        export_btn.connect("clicked", self._on_export_clicked)
        header.pack_end(export_btn)

        # Settings button
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic",
                                  tooltip_text=_("Settings"))
        settings_btn.connect("clicked", self._on_settings_clicked)
        header.pack_end(settings_btn)

        # About button
        about_btn = Gtk.Button(icon_name="help-about-symbolic",
                               tooltip_text=_("About"))
        about_btn.connect("clicked", self._on_about_clicked)
        header.pack_end(about_btn)

        # Theme toggle
        self._theme_btn = Gtk.Button(icon_name="weather-clear-night-symbolic",
                                     tooltip_text=_("Toggle dark/light theme"))
        self._theme_btn.connect("clicked", self._on_theme_toggle)
        header.pack_end(self._theme_btn)

        # Info button
        info_btn = Gtk.Button(icon_name="dialog-information-symbolic",
                              tooltip_text=_("How to help translate"))
        info_btn.connect("clicked", self._on_info_clicked)
        header.pack_end(info_btn)

        # Refresh button
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic",
                                 tooltip_text=_("Refresh data"))
        refresh_btn.connect("clicked", lambda _: self._load_data(force=True))
        header.pack_end(refresh_btn)

        # Content
        self._stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)

        # Loading view
        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                              valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        spinner = Gtk.Spinner(spinning=True, width_request=48, height_request=48)
        loading_box.append(spinner)
        loading_box.append(Gtk.Label(label=_("Loading translation data…")))
        self._stack.add_named(loading_box, "loading")

        # Error view
        self._error_label = Gtk.Label(wrap=True, halign=Gtk.Align.CENTER,
                                      valign=Gtk.Align.CENTER)
        self._stack.add_named(self._error_label, "error")

        # Data view - compact heatmap grid
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)

        self._flow_box = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            min_children_per_line=2,
            max_children_per_line=4,
            column_spacing=8,
            row_spacing=8,
            margin_top=16, margin_bottom=16,
            margin_start=16, margin_end=16,
        )

        scroll.set_child(self._flow_box)
        self._stack.add_named(scroll, "data")

        # Summary bar
        self._summary = Gtk.Label(halign=Gtk.Align.CENTER,
                                  margin_top=6, margin_bottom=6)
        self._summary.add_css_class("dim-label")

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(self._stack)
        content_box.append(self._summary)

        # Status bar
        self._status_bar = Gtk.Label(label="", halign=Gtk.Align.START,
                                     margin_start=12, margin_end=12, margin_bottom=4)
        self._status_bar.add_css_class("dim-label")
        self._status_bar.add_css_class("caption")
        content_box.append(self._status_bar)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(content_box)
        self.set_content(toolbar_view)

        # Load CSS
        self._setup_css()

        # Check for API key before making any requests
        config = weblate.load_config()
        if not config.get("api_key"):
            GLib.idle_add(self._show_api_key_setup)
        else:
            self._load_data()

    def _setup_css(self):
        css = b"""
        .card {
            border-radius: 12px;
            padding: 0;
            overflow: hidden;
        }
        .card:hover {
            opacity: 0.85;
        }
        .title-1 {
            font-size: 1.4em;
            font-weight: bold;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _load_data(self, force=False):
        self._stack.set_visible_child_name("loading")
        self._summary.set_text("")

        def on_data(rows):
            GLib.idle_add(self._populate, rows, False)

        def on_error(e):
            GLib.idle_add(self._show_error, str(e))

        def on_cache(rows, age_minutes):
            GLib.idle_add(self._populate, rows, True, age_minutes)

        weblate.fetch_all_data(
            self._current_lang, on_data, on_error,
            cache_cb=None if force else on_cache,
        )

    def _show_error(self, msg):
        self._error_label.set_markup(
            f"<b>{_('Failed to load data')}</b>\n\n{GLib.markup_escape_text(msg)}\n\n"
            f"{_('The Weblate instance might be temporarily unavailable.')}\n"
            f"{_('Click refresh to try again.')}"
        )
        self._stack.set_visible_child_name("error")

    def _populate(self, rows, from_cache=False, age_minutes=0):
        self._data = rows
        self._from_cache = from_cache
        self._cache_age = age_minutes
        # Notify about low translations
        low = [r["component"] for r in rows if r["translated_percent"] < 50 and r["translated_percent"] > 0]
        if low:
            _send_notification(
                _("elementary L10n: Low translations"),
                _("{count} components below 50%").format(count=len(low)),
                "se.danielnylander.TranslationStatus")
        self._render()

    def _render(self):
        # Clear
        while True:
            child = self._flow_box.get_first_child()
            if child is None:
                break
            self._flow_box.remove(child)

        # Apply status filter
        filter_key = self._filter_options[self._filter_dropdown.get_selected()][0]
        data = self._data
        if filter_key == "complete":
            data = [r for r in data if r["translated_percent"] >= 100]
        elif filter_key == "partial":
            data = [r for r in data if 0 < r["translated_percent"] < 100]
        elif filter_key == "untranslated":
            data = [r for r in data if r["translated_percent"] == 0]

        data = sorted(data, key=lambda r: r["translated_percent"],
                       reverse=not self._sort_ascending)

        if not data:
            self._show_error(_("No components found."))
            return

        avg = sum(r["translated_percent"] for r in data) / len(data)
        complete = sum(1 for r in data if r["translated_percent"] >= 100)
        summary = (
            _("{count} components · {complete} fully translated · "
              "Average: {avg}%").format(
                count=len(data), complete=complete, avg=f"{avg:.1f}")
        )
        if getattr(self, '_from_cache', False):
            summary += " · " + _("Cached data ({age} min ago)").format(
                age=self._cache_age)
        self._summary.set_text(summary)

        for row in data:
            self._flow_box.append(self._make_tile(row))

        self._stack.set_visible_child_name("data")
        self._update_status_bar()

    def _make_tile(self, item):
        """Create a compact heatmap tile for a component."""
        pct = item["translated_percent"]
        color = pct_to_color(pct)

        # Outer box as a clickable button-like tile
        tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                       width_request=200, height_request=80)
        tile.add_css_class("card")
        tile.set_margin_top(2)
        tile.set_margin_bottom(2)

        # Heatmap background
        bg = Gtk.DrawingArea(vexpand=True, hexpand=True)

        def draw_bg(area, cr, w, h, p=pct, c=color):
            # Background with heatmap color at low opacity
            cr.set_source_rgba(c.red, c.green, c.blue, 0.15)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            # Progress bar at bottom
            cr.set_source_rgba(c.red, c.green, c.blue, 0.7)
            cr.rectangle(0, h - 4, w * (p / 100), 4)
            cr.fill()
            # Track
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.15)
            cr.rectangle(w * (p / 100), h - 4, w - w * (p / 100), 4)
            cr.fill()

        bg.set_draw_func(draw_bg)

        # Overlay text on the drawing area
        overlay = Gtk.Overlay()
        overlay.set_child(bg)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2,
                           margin_top=8, margin_bottom=8,
                           margin_start=10, margin_end=10,
                           valign=Gtk.Align.CENTER)

        comp_label = Gtk.Label(
            label=item["component"],
            halign=Gtk.Align.START,
            ellipsize=Pango.EllipsizeMode.END,
            max_width_chars=25,
        )
        comp_label.add_css_class("heading")

        proj_label = Gtk.Label(
            label=item["project"],
            halign=Gtk.Align.START,
            ellipsize=Pango.EllipsizeMode.END,
            max_width_chars=25,
        )
        proj_label.add_css_class("dim-label")
        proj_label.add_css_class("caption")

        pct_label = Gtk.Label(
            label=f"{pct:.0f}%",
            halign=Gtk.Align.END,
            hexpand=True,
        )
        pct_label.add_css_class("numeric")
        pct_label.add_css_class("title-1")
        if pct >= 100:
            pct_label.add_css_class("success")

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        labels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels_box.append(comp_label)
        labels_box.append(proj_label)
        top_row.append(labels_box)
        top_row.append(pct_label)

        text_box.append(top_row)
        overlay.add_overlay(text_box)

        tile.append(overlay)

        # Make clickable
        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda g, n, x, y, url=item["translate_url"]: webbrowser.open(url))
        tile.add_controller(gesture)
        tile.set_cursor(Gdk.Cursor.new_from_name("pointer"))
        tile.set_tooltip_text(_("Open {component} on Weblate").format(
            component=item["component"]))

        return tile

    def _on_export_clicked(self, *_args):
        dialog = Adw.MessageDialog(transient_for=self,
                                   heading=_("Export Data"),
                                   body=_("Choose export format:"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("csv", "CSV")
        dialog.add_response("json", "JSON")
        dialog.set_response_appearance("csv", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_export_format_chosen)
        dialog.present()

    def _on_export_format_chosen(self, dialog, response):
        if response not in ("csv", "json"):
            return
        self._export_fmt = response
        fd = Gtk.FileDialog()
        fd.set_initial_name(f"translation-status.{response}")
        fd.save(self, None, self._on_export_save)

    def _on_export_save(self, dialog, result):
        try:
            path = dialog.save_finish(result).get_path()
        except Exception:
            return
        data = [{"project": r["project"], "component": r["component"],
                 "translated_percent": r["translated_percent"],
                 "translate_url": r["translate_url"]}
                for r in self._data]
        if self._export_fmt == "csv" and data:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=data[0].keys())
                w.writeheader()
                w.writerows(data)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


    def _on_theme_toggle(self, _btn):
        sm = Adw.StyleManager.get_default()
        if sm.get_color_scheme() == Adw.ColorScheme.FORCE_DARK:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self._theme_btn.set_icon_name("weather-clear-night-symbolic")
        else:
            sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self._theme_btn.set_icon_name("weather-clear-symbolic")

    def _update_status_bar(self):
        self._status_bar.set_text("Last updated: " + _dt_now.now().strftime("%Y-%m-%d %H:%M"))

    def _on_lang_changed(self, dropdown, _pspec):
        idx = dropdown.get_selected()
        if idx < len(self._lang_codes):
            self._current_lang = self._lang_codes[idx]
            self._load_data()

    def _on_filter_changed(self, _dropdown, _pspec):
        if self._data:
            self._render()

    def _on_sort_clicked(self, _btn):
        self._sort_ascending = not self._sort_ascending
        if self._data:
            self._render()

    def _show_api_key_setup(self):
        """Show first-run API key dialog. No requests are made until a key is provided."""
        self._stack.set_visible_child_name("error")
        self._error_label.set_markup(
            f"<b>{_('Weblate API Key Required')}</b>\n\n"
            f"{_('An API key is needed to fetch translation data.')}"
        )

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Welcome! API Key Required"),
            body=_(
                "To fetch translation status from Weblate, you need an API key.\n\n"
                "You can find your key at:\n"
                "https://l10n.elementaryos.org/accounts/profile/#api\n\n"
                "Log in (or create an account), then copy your API key below."
            ),
        )

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12)
        entry = Gtk.Entry(
            placeholder_text=_("Paste your API key here"),
            width_request=350,
        )
        link_btn = Gtk.LinkButton(
            uri="https://l10n.elementaryos.org/accounts/profile/#api",
            label=_("Open Weblate profile to get your API key"),
        )
        box.append(entry)
        box.append(link_btn)
        dialog.set_extra_child(box)

        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("save", _("Save & Continue"))
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response("cancel")

        def on_response(dlg, response):
            if response == "save":
                key = entry.get_text().strip()
                if key:
                    config = weblate.load_config()
                    config["api_key"] = key
                    weblate.save_config(config)
                    self._load_data()
                else:
                    # No key entered, show setup again
                    GLib.idle_add(self._show_api_key_setup)

        dialog.connect("response", on_response)
        dialog.present()

    def _on_toggle_notifications(self, _btn):
        config = _load_notify_config()
        config["enabled"] = not config.get("enabled", False)
        _save_notify_config(config)

    def _on_settings_clicked(self, _btn):
        """Show settings dialog for API key."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Settings"),
            body=_(
                "Enter your Weblate API key to avoid rate limiting.\n"
                "Find it at: l10n.elementaryos.org → Your profile → API access"
            ),
        )

        # Add entry for API key
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12)
        entry = Gtk.Entry(
            placeholder_text=_("Weblate API key"),
            width_request=300,
        )
        config = weblate.load_config()
        current_key = config.get("api_key", "")
        if current_key:
            entry.set_text(current_key)
        link_btn = Gtk.LinkButton(
            uri="https://l10n.elementaryos.org/accounts/profile/#api",
            label=_("Get your API key from Weblate"),
        )
        box.append(entry)
        box.append(link_btn)

        dialog.set_extra_child(box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("save", _("Save"))
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)

        def on_response(dlg, response):
            if response == "save":
                key = entry.get_text().strip()
                config = weblate.load_config()
                if key:
                    config["api_key"] = key
                else:
                    config.pop("api_key", None)
                weblate.save_config(config)
                # Reload with new key
                self._load_data(force=True)

        dialog.connect("response", on_response)
        dialog.present()

    def _on_about_clicked(self, _btn):
        about = Adw.AboutDialog(
            application_name=_("Translation Status"),
            application_icon="se.danielnylander.TranslationStatus",
            version="0.2.1",
            developer_name="Daniel Nylander",
            developers=["Daniel Nylander <daniel@danielnylander.se>"],
            copyright="© 2026 Daniel Nylander",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/yeager/elementary-l10n",
            issue_url="https://github.com/yeager/elementary-l10n/issues",
            translate_url="https://app.transifex.com/danielnylander/elementary-l10n/",
            comments=_("View translation status for elementary OS apps on Weblate. Track progress across languages and components."),
            translator_credits="Daniel Nylander <daniel@danielnylander.se>",
        )
        about.set_debug_info(_get_system_info())
        about.set_debug_info_filename("elementary-l10n-debug.txt")
        about.present(self)

    def _on_info_clicked(self, _btn):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Help Translate!"),
            body=_(
                "Translations are contributed by volunteers using "
                "Weblate — a web-based translation tool.\n\n"
                "Getting started is easy:\n\n"
                "1. Visit l10n.elementaryos.org\n"
                "2. Create a free account (or log in with GitHub)\n"
                "3. Pick a component and your language\n"
                "4. Start translating — no coding skills needed!\n\n"
                "Every translated string helps make software "
                "accessible to more people around the world. "
                "Even translating a few strings makes a difference."
            ),
        )
        dialog.add_response("close", _("Close"))
        dialog.add_response("open", _("Open Weblate"))
        dialog.set_response_appearance("open", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_info_response)
        dialog.present()

    def _on_info_response(self, dialog, response):
        if response == "open":
            webbrowser.open("https://l10n.elementaryos.org/")


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="se.danielnylander.TranslationStatus",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        if HAS_NOTIFY:
            _Notify.init("elementary-l10n")

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.set_accels_for_action("app.refresh", ["F5"])
        self.set_accels_for_action("app.shortcuts", ["<Control>slash"])
        for n, cb in [("quit", lambda *_: self.quit()),
                      ("refresh", lambda *_: self._do_refresh()),
                      ("shortcuts", self._show_shortcuts_window)]:
            a = Gio.SimpleAction.new(n, None); a.connect("activate", cb); self.add_action(a)

    def _do_refresh(self):
        w = self.get_active_window()
        if w: w._load_data(force=True)

    def _show_shortcuts_window(self, *_args):
        win = Gtk.ShortcutsWindow(transient_for=self.get_active_window(), modal=True)
        section = Gtk.ShortcutsSection(visible=True, max_height=10)
        group = Gtk.ShortcutsGroup(visible=True, title="General")
        for accel, title in [("<Control>q", "Quit"), ("F5", "Refresh"), ("<Control>slash", "Keyboard shortcuts")]:
            s = Gtk.ShortcutsShortcut(visible=True, accelerator=accel, title=title)
            group.append(s)
        section.append(group)
        win.add_child(section)
        win.present()

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = MainWindow(self)
        win.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.set_accels_for_action("app.export", ["<Control>e"])

        export_action = Gio.SimpleAction.new("export", None)
        export_action.connect("activate", self._on_export_activate)
        self.add_action(export_action)

    def _on_export_activate(self, *_args):
        win = self.get_active_window()
        if win:
            win._on_export_clicked()


def main():
    app = App()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
