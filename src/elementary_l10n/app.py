"""elementary OS Translation Status - GTK4/Adwaita app."""

import gettext
import locale
import os
import sys
import webbrowser

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
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


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=_("elementary OS Translation Status"),
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

        # Sort button
        sort_btn = Gtk.Button(icon_name="view-sort-descending-symbolic",
                              tooltip_text=_("Toggle sort order"))
        sort_btn.connect("clicked", self._on_sort_clicked)
        header.pack_start(sort_btn)

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

        # Data view - scrolled list
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self._list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self._list_box.add_css_class("boxed-list")

        clamp = Adw.Clamp(maximum_size=800, child=self._list_box,
                          margin_top=24, margin_bottom=24,
                          margin_start=12, margin_end=12)
        scroll.set_child(clamp)
        self._stack.add_named(scroll, "data")

        # Summary bar
        self._summary = Gtk.Label(halign=Gtk.Align.CENTER,
                                  margin_top=6, margin_bottom=6)
        self._summary.add_css_class("dim-label")

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(self._stack)
        content_box.append(self._summary)

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
        .pct-bar {
            border-radius: 6px;
            min-height: 8px;
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
        self._render()

    def _render(self):
        # Clear
        while True:
            child = self._list_box.get_first_child()
            if child is None:
                break
            self._list_box.remove(child)

        data = sorted(self._data, key=lambda r: r["translated_percent"],
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
            self._list_box.append(self._make_row(row))

        self._stack.set_visible_child_name("data")

    def _make_row(self, item):
        row = Adw.ActionRow(
            title=GLib.markup_escape_text(item["component"]),
            subtitle=GLib.markup_escape_text(item["project"]),
            activatable=True,
        )
        row.set_tooltip_text(_("Open {component} on Weblate").format(
            component=item['component']))
        row.connect("activated", lambda _, url=item["translate_url"]: webbrowser.open(url))
        row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))

        # Percentage + color bar
        pct = item["translated_percent"]
        color = pct_to_color(pct)

        pct_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2,
                          valign=Gtk.Align.CENTER, width_request=80)

        pct_label = Gtk.Label(label=f"{pct:.0f}%", halign=Gtk.Align.END)
        pct_label.add_css_class("numeric")
        if pct >= 100:
            pct_label.add_css_class("success")

        bar = Gtk.DrawingArea(width_request=80, height_request=8)
        bar.add_css_class("pct-bar")

        def draw_bar(area, cr, w, h, p=pct, c=color):
            cr.set_source_rgba(0.3, 0.3, 0.3, 0.3)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_source_rgba(c.red, c.green, c.blue, c.alpha)
            cr.rectangle(0, 0, w * (p / 100), h)
            cr.fill()

        bar.set_draw_func(draw_bar)

        pct_box.append(pct_label)
        pct_box.append(bar)
        row.add_suffix(pct_box)

        return row

    def _on_lang_changed(self, dropdown, _pspec):
        idx = dropdown.get_selected()
        if idx < len(self._lang_codes):
            self._current_lang = self._lang_codes[idx]
            self._load_data()

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
        about = Adw.AboutWindow(
            transient_for=self,
            application_name=_("elementary OS Translation Status"),
            application_icon="elementary-l10n",
            version="0.1.0",
            developer_name="Daniel Nylander",
            developers=["Daniel Nylander <daniel@danielnylander.se>"],
            copyright="© 2025 Daniel Nylander",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/yeager/elementary-l10n",
            issue_url="https://github.com/yeager/elementary-l10n/issues",
            comments=_("A localization tool by Daniel Nylander"),
            translator_credits=_("Translate this app: https://app.transifex.com/linguaedit/elementary-l10n/"),
        )
        about.present()

    def _on_info_clicked(self, _btn):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Help Translate elementary OS!"),
            body=_(
                "elementary OS is translated by volunteers like you using "
                "Weblate — a web-based translation tool.\n\n"
                "Getting started is easy:\n\n"
                "1. Visit l10n.elementaryos.org\n"
                "2. Create a free account (or log in with GitHub)\n"
                "3. Pick a component and your language\n"
                "4. Start translating — no coding skills needed!\n\n"
                "Every translated string helps make elementary OS "
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
        super().__init__(application_id="io.github.yeager.elementary-l10n",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = MainWindow(self)
        win.present()


def main():
    app = App()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
