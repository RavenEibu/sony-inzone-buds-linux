#!/usr/bin/env python3
"""GTK4 application for controlling the INZONE Buds audio endpoints."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from audio import AudioBackend, AudioSnapshot, BackendError  # noqa: E402
from tray import StatusNotifierItem  # noqa: E402


APP_ID = "io.github.RavenEibu.InzoneBudsMixer"
APP_NAME = "INZONE Buds Mixer"
ICON_NAME = APP_ID
PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
PORTAL_SETTINGS_INTERFACE = "org.freedesktop.portal.Settings"
PORTAL_APPEARANCE_NAMESPACE = "org.freedesktop.appearance"
PORTAL_COLOR_SCHEME_KEY = "color-scheme"
APP_CSS = """
window.inzone-light,
window.inzone-light headerbar {
  background-color: #f7f7f8;
  color: #202124;
}

window.inzone-dark,
window.inzone-dark headerbar {
  background-color: #202124;
  color: #f5f5f5;
}
"""


def _margins(widget: Gtk.Widget, amount: int) -> None:
    widget.set_margin_top(amount)
    widget.set_margin_bottom(amount)
    widget.set_margin_start(amount)
    widget.set_margin_end(amount)


class MixerWindow(Gtk.ApplicationWindow):
    def __init__(self, application: "MixerApplication", backend: AudioBackend) -> None:
        super().__init__(application=application, title=APP_NAME)
        self.application = application
        self.backend = backend
        self._updating = False
        self._balance_timer = 0
        self._mic_timer = 0
        self.set_default_size(520, 540)
        self.set_resizable(False)
        self.connect("close-request", self._close_requested)

        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh.set_tooltip_text("Refresh device status")
        refresh.connect("clicked", lambda _button: self.application.refresh())
        header.pack_start(refresh)

        quit_button = Gtk.Button.new_from_icon_name("application-exit-symbolic")
        quit_button.set_tooltip_text("Quit")
        quit_button.connect("clicked", lambda _button: self.application.quit())
        header.pack_end(quit_button)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        _margins(root, 24)
        self.set_child(root)

        title = Gtk.Label(label="Game / Chat audio")
        title.set_xalign(0)
        title.add_css_class("title-2")
        root.append(title)

        self.status = Gtk.Label(label="Checking for the PC-mode dongle…")
        self.status.set_xalign(0)
        self.status.set_wrap(True)
        root.append(self.status)

        self.overall_scale, self.overall_value = self._add_scale(
            root,
            "Overall volume",
            "Limits the louder Game/Chat endpoint. At center, both use this volume.",
            self._balance_changed,
        )

        self.balance_scale, self.balance_value = self._add_scale(
            root,
            "Game / Chat balance",
            "0 = Chat, 50 = both equally, 100 = Game",
            self._balance_changed,
        )
        self.balance_scale.add_mark(0, Gtk.PositionType.BOTTOM, "Chat")
        self.balance_scale.add_mark(50, Gtk.PositionType.BOTTOM, "Both")
        self.balance_scale.add_mark(100, Gtk.PositionType.BOTTOM, "Game")

        self.mic_scale, self.mic_value = self._add_scale(
            root,
            "Microphone volume",
            "Input level sent to voice applications.",
            self._microphone_changed,
        )

        self.defaults_button = Gtk.Button(label="Use Game output + INZONE microphone")
        self.defaults_button.add_css_class("suggested-action")
        self.defaults_button.connect("clicked", self._select_defaults)
        root.append(self.defaults_button)

        self.endpoint_status = Gtk.Label()
        self.endpoint_status.set_xalign(0)
        self.endpoint_status.set_wrap(True)
        self.endpoint_status.add_css_class("dim-label")
        root.append(self.endpoint_status)

        self.tray_status = Gtk.Label(label="Tray integration: checking…")
        self.tray_status.set_xalign(0)
        self.tray_status.add_css_class("dim-label")
        root.append(self.tray_status)

    def _add_scale(self, parent, heading, description, callback):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=heading)
        label.set_xalign(0)
        label.set_hexpand(True)
        value = Gtk.Label(label="—")
        row.append(label)
        row.append(value)
        section.append(row)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        scale.set_draw_value(False)
        scale.set_hexpand(True)
        scale.connect("value-changed", callback)
        section.append(scale)

        hint = Gtk.Label(label=description)
        hint.set_xalign(0)
        hint.set_wrap(True)
        hint.add_css_class("dim-label")
        section.append(hint)
        parent.append(section)
        return scale, value

    def _close_requested(self, _window) -> bool:
        if self.application.tray_available:
            self.set_visible(False)
            return True
        return False

    def set_tray_available(self, available: bool) -> None:
        if available:
            self.tray_status.set_label("Tray integration active — closing hides this window.")
        else:
            self.tray_status.set_label(
                "Tray icon unavailable — install/enable AppIndicator support in GNOME."
            )

    def show_error(self, message: str) -> None:
        self.status.set_label(f"Audio control error: {message}")
        self.status.add_css_class("error")

    def apply_snapshot(self, snapshot: AudioSnapshot) -> None:
        self._updating = True
        self.status.remove_css_class("error")
        if snapshot.connected:
            self.status.set_label("● INZONE Buds connected in PC mode")
            self.status.add_css_class("success")
        else:
            self.status.set_label(
                "INZONE Buds PC-mode endpoints are unavailable. Connect the dongle "
                "with its switch set to PC."
            )
            self.status.remove_css_class("success")

        self.overall_scale.set_value(snapshot.overall_volume)
        self.balance_scale.set_value(snapshot.balance)
        self.mic_scale.set_value(snapshot.microphone_volume or 0)
        self._update_value_labels()

        controls = (self.overall_scale, self.balance_scale, self.mic_scale, self.defaults_button)
        for control in controls:
            control.set_sensitive(snapshot.connected)

        output = "Game" if snapshot.default_sink == snapshot.game else "another device"
        microphone = (
            "INZONE microphone"
            if snapshot.default_source == snapshot.microphone
            else "another device"
        )
        self.endpoint_status.set_label(
            f"Game {snapshot.game_volume if snapshot.game_volume is not None else '—'}%  ·  "
            f"Chat {snapshot.chat_volume if snapshot.chat_volume is not None else '—'}%  ·  "
            f"Default output: {output}  ·  Default input: {microphone}"
        )
        self._updating = False

    def _update_value_labels(self) -> None:
        self.overall_value.set_label(f"{round(self.overall_scale.get_value())}%")
        self.balance_value.set_label(str(round(self.balance_scale.get_value())))
        self.mic_value.set_label(f"{round(self.mic_scale.get_value())}%")

    def _balance_changed(self, _scale) -> None:
        self._update_value_labels()
        if self._updating:
            return
        if self._balance_timer:
            GLib.source_remove(self._balance_timer)
        self._balance_timer = GLib.timeout_add(140, self._commit_balance)

    def _commit_balance(self) -> bool:
        self._balance_timer = 0
        position = round(self.balance_scale.get_value())
        maximum = round(self.overall_scale.get_value())
        self.application.run_audio_action(self.backend.set_balance, position, maximum)
        return GLib.SOURCE_REMOVE

    def _microphone_changed(self, _scale) -> None:
        self._update_value_labels()
        if self._updating:
            return
        if self._mic_timer:
            GLib.source_remove(self._mic_timer)
        self._mic_timer = GLib.timeout_add(140, self._commit_microphone)

    def _commit_microphone(self) -> bool:
        self._mic_timer = 0
        volume = round(self.mic_scale.get_value())
        self.application.run_audio_action(self.backend.set_microphone_volume, volume)
        return GLib.SOURCE_REMOVE

    def _select_defaults(self, _button) -> None:
        self.application.run_audio_action(self.backend.select_defaults)


class MixerApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.backend = AudioBackend()
        self.window: MixerWindow | None = None
        self.tray: StatusNotifierItem | None = None
        self.tray_available = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="inzone-audio")
        self._refresh_in_progress = False
        self._poll_id = 0
        self._held = False
        self._gtk_settings = None
        self._portal_settings = None
        self._portal_color_scheme: int | None = None
        self._applying_color_scheme = False
        self._css_provider = None

    def do_activate(self) -> None:
        if self.window is None:
            self._install_css()
            self.window = MixerWindow(self, self.backend)
            self._watch_color_scheme()
            self._start_tray()
            self._poll_id = GLib.timeout_add_seconds(2, self._poll)
        self.window.present()
        self.refresh()

    def _start_tray(self) -> None:
        xdg_data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        icon_theme_path = os.environ.get(
            "INZONE_BUDS_MIXER_ICON_THEME_PATH",
            str(xdg_data_home / "icons"),
        )
        try:
            self.tray = StatusNotifierItem(
                icon_name=ICON_NAME,
                icon_theme_path=icon_theme_path,
                on_activate=self.toggle_window,
                on_quit=self.quit,
                on_availability_changed=self._tray_changed,
            )
        except GLib.Error:
            self._tray_changed(False)

    def _tray_changed(self, available: bool) -> bool:
        self.tray_available = available
        if available and not self._held:
            self.hold()
            self._held = True
        if self.window:
            self.window.set_tray_available(available)
        return GLib.SOURCE_REMOVE

    def toggle_window(self) -> bool:
        if not self.window:
            self.activate()
        elif self.window.get_visible():
            self.window.set_visible(False)
        else:
            self.window.present()
            self.refresh()
        return GLib.SOURCE_REMOVE

    def _watch_color_scheme(self) -> None:
        self._gtk_settings = Gtk.Settings.get_default()
        if self._gtk_settings:
            for property_name in (
                "gtk-interface-color-scheme",
                "gtk-application-prefer-dark-theme",
                "gtk-theme-name",
            ):
                if self._gtk_settings.find_property(property_name):
                    self._gtk_settings.connect(
                        f"notify::{property_name}",
                        self._color_scheme_changed,
                    )
        self._watch_portal_color_scheme()
        self._apply_detected_color_scheme()

    def _watch_portal_color_scheme(self) -> None:
        try:
            self._portal_settings = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                PORTAL_BUS_NAME,
                PORTAL_OBJECT_PATH,
                PORTAL_SETTINGS_INTERFACE,
                None,
            )
            self._portal_settings.connect("g-signal", self._portal_setting_changed)
            self._read_portal_color_scheme()
        except GLib.Error:
            self._portal_settings = None
            self._portal_color_scheme = None

    @staticmethod
    def _unpack_portal_value(value):
        while value.get_type_string() == "v":
            value = value.get_variant()
        return value.unpack()

    def _read_portal_color_scheme(self) -> None:
        if not self._portal_settings:
            return
        parameters = GLib.Variant(
            "(ss)",
            (PORTAL_APPEARANCE_NAMESPACE, PORTAL_COLOR_SCHEME_KEY),
        )
        for method_name in ("ReadOne", "Read"):
            try:
                result = self._portal_settings.call_sync(
                    method_name,
                    parameters,
                    Gio.DBusCallFlags.NONE,
                    2000,
                    None,
                )
            except GLib.Error:
                continue
            value = self._unpack_portal_value(result.get_child_value(0))
            if isinstance(value, int):
                self._portal_color_scheme = value
                return

    def _portal_setting_changed(
        self,
        _proxy,
        _sender_name,
        signal_name: str,
        parameters,
    ) -> None:
        if signal_name != "SettingChanged":
            return
        namespace = parameters.get_child_value(0).unpack()
        key = parameters.get_child_value(1).unpack()
        if (
            namespace != PORTAL_APPEARANCE_NAMESPACE
            or key != PORTAL_COLOR_SCHEME_KEY
        ):
            return
        value = self._unpack_portal_value(parameters.get_child_value(2))
        if isinstance(value, int):
            self._portal_color_scheme = value
            self._apply_detected_color_scheme()

    def _install_css(self) -> None:
        display = Gdk.Display.get_default()
        if not display:
            return
        self._css_provider = Gtk.CssProvider()
        self._css_provider.load_from_data(APP_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            display,
            self._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _color_scheme_changed(self, _settings, _parameter) -> None:
        self._apply_detected_color_scheme()

    def _detect_dark_mode(self) -> bool:
        # XDG Desktop Portal uses 1 for dark, 2 for light and 0 for the normal
        # desktop appearance. GNOME reports its light mode as 0, so it must be
        # treated as light instead of falling back to a stale GTK preference.
        if self._portal_color_scheme in (0, 1, 2):
            return self._portal_color_scheme == 1

        settings = self._gtk_settings
        if not settings:
            return False

        if settings.find_property("gtk-interface-color-scheme"):
            # GTK 4.20+: 2 is dark and 3 is light. Other values mean that the
            # platform did not provide an explicit preference.
            scheme = int(settings.get_property("gtk-interface-color-scheme"))
            if scheme == 2:
                return True
            if scheme == 3:
                return False

        theme_name = str(settings.get_property("gtk-theme-name") or "").lower()
        if "dark" in theme_name:
            return True
        if settings.find_property("gtk-application-prefer-dark-theme"):
            return bool(settings.get_property("gtk-application-prefer-dark-theme"))
        return False

    def _apply_detected_color_scheme(self) -> None:
        if self._applying_color_scheme:
            return
        self._applying_color_scheme = True
        try:
            dark = self._detect_dark_mode()
            if self.window:
                self.window.remove_css_class("inzone-dark")
                self.window.remove_css_class("inzone-light")
                self.window.add_css_class("inzone-dark" if dark else "inzone-light")
        finally:
            self._applying_color_scheme = False

    def _poll(self) -> bool:
        self.refresh()
        return GLib.SOURCE_CONTINUE

    def refresh(self) -> None:
        if self._refresh_in_progress:
            return
        self._refresh_in_progress = True
        future = self._executor.submit(self.backend.snapshot)
        future.add_done_callback(lambda result: GLib.idle_add(self._finish_refresh, result))

    def _finish_refresh(self, future) -> bool:
        self._refresh_in_progress = False
        if not self.window:
            return GLib.SOURCE_REMOVE
        try:
            snapshot = future.result()
        except (BackendError, OSError) as error:
            self.window.show_error(str(error))
        else:
            self.window.apply_snapshot(snapshot)
        return GLib.SOURCE_REMOVE

    def run_audio_action(self, operation, *arguments) -> None:
        future = self._executor.submit(operation, *arguments)
        future.add_done_callback(lambda result: GLib.idle_add(self._finish_action, result))

    def _finish_action(self, future) -> bool:
        try:
            future.result()
        except (BackendError, OSError) as error:
            if self.window:
                self.window.show_error(str(error))
        self.refresh()
        return GLib.SOURCE_REMOVE

    def do_shutdown(self) -> None:
        if self._poll_id:
            GLib.source_remove(self._poll_id)
            self._poll_id = 0
        if self.tray:
            self.tray.close()
        self._executor.shutdown(wait=False, cancel_futures=True)
        Gtk.Application.do_shutdown(self)


def main() -> int:
    application = MixerApplication()
    return application.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
