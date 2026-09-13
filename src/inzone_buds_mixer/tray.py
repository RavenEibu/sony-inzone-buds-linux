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

DBUSMENU_XML = """
<node>
  <interface name="com.canonical.dbusmenu">
    <method name="GetLayout">
      <arg type="i" direction="in" name="parentId"/>
      <arg type="i" direction="in" name="recursionDepth"/>
      <arg type="as" direction="in" name="propertyNames"/>
      <arg type="u" direction="out" name="revision"/>
      <arg type="(ia{sv}av)" direction="out" name="layout"/>
    </method>
    <method name="GetGroupProperties">
      <arg type="ai" direction="in" name="ids"/>
      <arg type="as" direction="in" name="propertyNames"/>
      <arg type="a(ia{sv})" direction="out" name="properties"/>
    </method>
    <method name="GetProperty">
      <arg type="i" direction="in" name="id"/>
      <arg type="s" direction="in" name="name"/>
      <arg type="v" direction="out" name="value"/>
    </method>
    <method name="Event">
      <arg type="i" direction="in" name="id"/>
      <arg type="s" direction="in" name="eventId"/>
      <arg type="v" direction="in" name="data"/>
      <arg type="u" direction="in" name="timestamp"/>
    </method>
    <method name="EventGroup">
      <arg type="a(isvu)" direction="in" name="events"/>
      <arg type="ai" direction="out" name="idErrors"/>
    </method>
    <method name="AboutToShow">
      <arg type="i" direction="in" name="id"/>
      <arg type="b" direction="out" name="needUpdate"/>
    </method>
    <method name="AboutToShowGroup">
      <arg type="ai" direction="in" name="ids"/>
      <arg type="ai" direction="out" name="updatesNeeded"/>
      <arg type="ai" direction="out" name="idErrors"/>
    </method>
    <property name="Version" type="u" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <signal name="ItemsPropertiesUpdated">
      <arg type="a(ia{sv})" name="updatedProps"/>
      <arg type="a(ias)" name="removedProps"/>
    </signal>
    <signal name="LayoutUpdated">
      <arg type="u" name="revision"/>
      <arg type="i" name="parent"/>
    </signal>
  </interface>
</node>
"""


class StatusNotifierItem:
    """Export a clickable tray icon when an SNI watcher is available."""

    WATCHER_NAME = "org.kde.StatusNotifierWatcher"
    WATCHER_PATH = "/StatusNotifierWatcher"
    WATCHER_INTERFACE = "org.kde.StatusNotifierWatcher"
    ITEM_PATH = "/StatusNotifierItem"
    MENU_PATH = "/MenuBar"

    def __init__(
        self,
        *,
        icon_name: str,
        icon_theme_path: str,
        on_activate: Callable[[], None],
        on_quit: Callable[[], None],
        on_availability_changed: Callable[[bool], None] | None = None,
    ) -> None:
        self.icon_name = icon_name
        self.icon_theme_path = icon_theme_path
        self.on_activate = on_activate
        self.on_quit = on_quit
        self.on_availability_changed = on_availability_changed
        self.available = False
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.bus_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
        self._node_info = Gio.DBusNodeInfo.new_for_xml(SNI_XML)
        self._menu_node_info = Gio.DBusNodeInfo.new_for_xml(DBUSMENU_XML)
        self._registration_id = self.connection.register_object(
            self.ITEM_PATH,
            self._node_info.interfaces[0],
            self._handle_method,
            self._get_property,
            None,
        )
        self._menu_registration_id = self.connection.register_object(
            self.MENU_PATH,
            self._menu_node_info.interfaces[0],
            self._handle_menu_method,
            self._get_menu_property,
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
        if method_name in ("Activate", "SecondaryActivate"):
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
            "Menu": GLib.Variant("o", self.MENU_PATH),
        }
        return properties.get(property_name)

    @staticmethod
    def _all_menu_properties(item_id: int) -> dict[str, GLib.Variant]:
        if item_id == 0:
            return {"children-display": GLib.Variant("s", "submenu")}
        if item_id == 1:
            return {
                "label": GLib.Variant("s", "Show Window"),
                "enabled": GLib.Variant("b", True),
                "visible": GLib.Variant("b", True),
            }
        if item_id == 2:
            return {
                "type": GLib.Variant("s", "separator"),
                "visible": GLib.Variant("b", True),
            }
        if item_id == 3:
            return {
                "label": GLib.Variant("s", "Quit"),
                "enabled": GLib.Variant("b", True),
                "visible": GLib.Variant("b", True),
            }
        return {}

    @classmethod
    def _menu_properties(
        cls,
        item_id: int,
        requested: list[str] | tuple[str, ...],
    ) -> dict[str, GLib.Variant]:
        properties = cls._all_menu_properties(item_id)
        if not requested:
            return properties
        return {name: value for name, value in properties.items() if name in requested}

    @classmethod
    def _menu_layout(cls, item_id: int, depth: int, requested):
        children = []
        if item_id == 0 and depth != 0:
            children = [
                GLib.Variant(
                    "(ia{sv}av)",
                    (child_id, cls._menu_properties(child_id, requested), []),
                )
                for child_id in (1, 2, 3)
            ]
        return (item_id, cls._menu_properties(item_id, requested), children)

    def _activate_menu_item(self, item_id: int, event_id: str) -> None:
        if event_id != "clicked":
            return
        if item_id == 1:
            GLib.idle_add(self.on_activate)
        elif item_id == 3:
            GLib.idle_add(self.on_quit)

    def _handle_menu_method(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        method_name,
        parameters,
        invocation,
    ) -> None:
        values = parameters.unpack()
        if method_name == "GetLayout":
            parent_id, depth, requested = values
            layout = self._menu_layout(parent_id, depth, requested)
            invocation.return_value(GLib.Variant("(u(ia{sv}av))", (1, layout)))
        elif method_name == "GetGroupProperties":
            item_ids, requested = values
            rows = [
                (item_id, self._menu_properties(item_id, requested))
                for item_id in item_ids
            ]
            invocation.return_value(GLib.Variant("(a(ia{sv}))", (rows,)))
        elif method_name == "GetProperty":
            item_id, name = values
            value = self._all_menu_properties(item_id).get(name, GLib.Variant("s", ""))
            invocation.return_value(GLib.Variant("(v)", (value,)))
        elif method_name == "Event":
            item_id, event_id, _data, _timestamp = values
            self._activate_menu_item(item_id, event_id)
            invocation.return_value(None)
        elif method_name == "EventGroup":
            for item_id, event_id, _data, _timestamp in values[0]:
                self._activate_menu_item(item_id, event_id)
            invocation.return_value(GLib.Variant("(ai)", ([],)))
        elif method_name == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))
        elif method_name == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))

    def _get_menu_property(
        self,
        _connection,
        _sender,
        _object_path,
        _interface_name,
        property_name,
    ):
        properties = {
            "Version": GLib.Variant("u", 3),
            "TextDirection": GLib.Variant("s", "ltr"),
            "Status": GLib.Variant("s", "normal"),
            "IconThemePath": GLib.Variant("as", [self.icon_theme_path]),
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
        if self._menu_registration_id:
            self.connection.unregister_object(self._menu_registration_id)
            self._menu_registration_id = 0
