"""Minimal StatusNotifierItem implementation using GIO's D-Bus API."""

from __future__ import annotations

import os
from typing import Callable

from gi.repository import Gio, GLib


SNI_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <method name="ContextMenu">
      <arg type="i" direction="in" name="x"/>
      <arg type="i" direction="in" name="y"/>
    </method>
    <method name="Activate">
      <arg type="i" direction="in" name="x"/>
      <arg type="i" direction="in" name="y"/>
    </method>
    <method name="SecondaryActivate">
      <arg type="i" direction="in" name="x"/>
      <arg type="i" direction="in" name="y"/>
    </method>
    <method name="Scroll">
      <arg type="i" direction="in" name="delta"/>
      <arg type="s" direction="in" name="orientation"/>
    </method>
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="u" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <signal name="NewIcon"/>
    <signal name="NewStatus"><arg type="s"/></signal>
  </interface>
</node>
"""


class StatusNotifierItem:
    """Export a clickable tray icon when an SNI watcher is available."""

    WATCHER_NAME = "org.kde.StatusNotifierWatcher"
    WATCHER_PATH = "/StatusNotifierWatcher"
    WATCHER_INTERFACE = "org.kde.StatusNotifierWatcher"
    ITEM_PATH = "/StatusNotifierItem"

    def __init__(
        self,
        *,
        icon_name: str,
        icon_theme_path: str,
        on_activate: Callable[[], None],
        on_availability_changed: Callable[[bool], None] | None = None,
    ) -> None:
        self.icon_name = icon_name
        self.icon_theme_path = icon_theme_path
        self.on_activate = on_activate
        self.on_availability_changed = on_availability_changed
        self.available = False
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.bus_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        self._node_info = Gio.DBusNodeInfo.new_for_xml(SNI_XML)
        self._registration_id = self.connection.register_object(
            self.ITEM_PATH,
            self._node_info.interfaces[0],
            self._handle_method,
            self._get_property,
            None,
        )
        self._owner_id = Gio.bus_own_name_on_connection(
            self.connection,
            self.bus_name,
            Gio.BusNameOwnerFlags.NONE,
            None,
            None,
        )
        self._watch_id = Gio.bus_watch_name(
            Gio.BusType.SESSION,
            self.WATCHER_NAME,
            Gio.BusNameWatcherFlags.NONE,
            self._watcher_appeared,
            self._watcher_vanished,
        )

    def _set_available(self, value: bool) -> None:
        if self.available == value:
            return
        self.available = value
        if self.on_availability_changed:
            GLib.idle_add(self.on_availability_changed, value)

    def _watcher_appeared(self, _connection, _name, _owner) -> None:
        try:
            self.connection.call_sync(
                self.WATCHER_NAME,
                self.WATCHER_PATH,
                self.WATCHER_INTERFACE,
                "RegisterStatusNotifierItem",
                GLib.Variant("(s)", (self.bus_name,)),
                None,
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except GLib.Error:
            self._set_available(False)
        else:
            self._set_available(True)

    def _watcher_vanished(self, _connection, _name) -> None:
        self._set_available(False)

    def _handle_method(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        method_name,
        _parameters,
        invocation,
    ) -> None:
        if method_name in ("Activate", "SecondaryActivate", "ContextMenu"):
            GLib.idle_add(self.on_activate)
        invocation.return_value(None)

    def _get_property(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        property_name,
    ):
        properties = {
            "Category": GLib.Variant("s", "Hardware"),
            "Id": GLib.Variant("s", "inzone-buds-mixer"),
            "Title": GLib.Variant("s", "INZONE Buds Mixer"),
            "Status": GLib.Variant("s", "Active"),
            "WindowId": GLib.Variant("u", 0),
            "IconName": GLib.Variant("s", self.icon_name),
            "IconThemePath": GLib.Variant("s", self.icon_theme_path),
            "AttentionIconName": GLib.Variant("s", ""),
            "OverlayIconName": GLib.Variant("s", ""),
            "ItemIsMenu": GLib.Variant("b", False),
            "Menu": GLib.Variant("o", "/NO_DBUSMENU"),
        }
        return properties.get(property_name)

    def close(self) -> None:
        if self._watch_id:
            Gio.bus_unwatch_name(self._watch_id)
            self._watch_id = 0
        if self._owner_id:
            Gio.bus_unown_name(self._owner_id)
            self._owner_id = 0
        if self._registration_id:
            self.connection.unregister_object(self._registration_id)
            self._registration_id = 0
