#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_zigbee2mqtt_contract.py
# Description: How Water Leak Monitor reads the states Zigbee2MQTT Bridge writes
#              on a z2mWaterLeakSensor (bridge 2.20.1):
#                * waterLeak            Boolean, the leak reading
#                * onOffState           mirrors waterLeak
#                * Indigo error state   "offline" (zigbee2mqtt's verdict) or
#                                       "bridge down" (bridge unreachable > 3 min)
#              The error state is the ONLY signal this plugin uses for a dead
#              sensor, so any error text must count — not just "offline".
# Author:      CliveS & Claude
# Date:        01-11-2026
# Version:     1.0

from unittest.mock import MagicMock

import pytest

from _harness import FakeSensor, SENSOR_ID, indigo_stub, make_plugin, reset_server, wlm


@pytest.fixture
def setup():
    reset_server()
    wlm.QUICK_RETEST_DELAY  = 0
    wlm.ALERT_RETRY_BACKOFF = 0
    sensor = FakeSensor(name="Utility Leak", states={"waterLeak": False,
                                                    "onOffState": False})
    indigo_stub.devices[SENSOR_ID] = sensor
    pushover = MagicMock()
    pushover.isEnabled.return_value = True
    indigo_stub.server.getPlugin.return_value = pushover
    yield make_plugin(), sensor, pushover
    indigo_stub.devices.pop(SENSOR_ID, None)


def _urgent_alerts(pushover):
    return [c for c in pushover.executeAction.call_args_list
            if c.kwargs["props"]["msgPriority"] == "1"]


@pytest.mark.parametrize("error", ["offline", "bridge down"])
def test_any_bridge_error_counts_as_not_answering(setup, error):
    plugin, sensor, pushover = setup
    sensor.errorState = error
    plugin._check_leak_sensor()
    assert pushover.executeAction.call_count == 1
    assert error in indigo_stub.server.sendEmailTo.call_args.kwargs["body"]


@pytest.mark.parametrize("error", ["offline", "bridge down"])
def test_a_sensor_in_error_is_not_read_for_a_leak(setup, error):
    """Its states are the last ones heard, not live: no leak alert from them."""
    plugin, sensor, pushover = setup
    sensor.errorState = error
    sensor.states["waterLeak"] = True
    plugin._check_leak_sensor()
    assert _urgent_alerts(pushover) == []


def test_waterleak_wins_over_onoffstate(setup):
    plugin, sensor, pushover = setup
    sensor.states["waterLeak"] = True
    sensor._on = False
    plugin._check_leak_sensor()
    assert len(_urgent_alerts(pushover)) == 1


def test_availability_state_alone_is_not_the_signal(setup):
    """Documents the contract: an `availability` state of "offline" WITHOUT
    the Indigo error is still read as live. The bridge always sets both."""
    plugin, sensor, pushover = setup
    sensor.states["availability"] = "offline"
    sensor.states["waterLeak"] = True
    plugin._check_leak_sensor()
    assert len(_urgent_alerts(pushover)) == 1


def test_an_outage_during_a_leak_alerts_again_when_it_ends(setup):
    """Wet and alerted -> bridge down -> back and still wet: alerted again,
    so a leak that outlasts an outage is not forgotten."""
    plugin, sensor, pushover = setup
    sensor.states["waterLeak"] = True
    plugin._check_leak_sensor()
    assert len(_urgent_alerts(pushover)) == 1
    sensor.errorState = "bridge down"
    plugin._check_leak_sensor()
    sensor.errorState = None
    plugin._check_leak_sensor()
    assert len(_urgent_alerts(pushover)) == 2


def test_the_back_notice_follows_the_bridge_returning(setup):
    plugin, sensor, pushover = setup
    sensor.errorState = "bridge down"
    plugin._check_leak_sensor()
    sensor.errorState = None
    plugin._check_leak_sensor()
    titles = [c.kwargs["props"]["msgTitle"] for c in pushover.executeAction.call_args_list]
    assert titles == ["Leak sensor not answering", "Leak sensor back"]


# ── preferences read back from Indigo ───────────────────────────────────────

def _plugin_with(monkeypatch, prefs):
    monkeypatch.setattr(wlm, "install_timestamp_filter", None)
    monkeypatch.setattr(wlm.Plugin, "logger", MagicMock(), raising=False)
    return wlm.Plugin("id", "Water Leak Monitor", "1.10.1",
                      {"alertEmail": "x@example.com", **prefs})


def test_timestamp_pref_stored_as_the_string_false_is_off(monkeypatch):
    """Fixed in 1.10.1: was bool(), so "false" read as on."""
    monkeypatch.setattr(wlm, "install_timestamp_filter", None)
    monkeypatch.setattr(wlm.Plugin, "logger", MagicMock(), raising=False)
    plugin = wlm.Plugin("id", "Water Leak Monitor", "1.10.0",
                        {"timestampEnabled": "false", "alertEmail": "x@example.com"})
    assert plugin.timestamp_enabled is False


@pytest.mark.parametrize("stored,expected", [
    (True, True), (False, False), ("true", True), ("false", False),
    ("", True), (None, True), ("junk", True),
])
def test_timestamp_pref_reads(monkeypatch, stored, expected):
    """Unset or unreadable keeps the default (on)."""
    prefs = {} if stored is None else {"timestampEnabled": stored}
    assert _plugin_with(monkeypatch, prefs).timestamp_enabled is expected


@pytest.mark.parametrize("stored,expected", [
    (True, True), (False, False), ("true", True), ("false", False), ("", False),
])
def test_debug_pref_reads(monkeypatch, stored, expected):
    assert _plugin_with(monkeypatch, {"showDebugInfo": stored}).debug is expected


def test_debug_pref_from_the_configure_dialog(monkeypatch):
    plugin = _plugin_with(monkeypatch, {})
    plugin.closedPrefsConfigUi({"showDebugInfo": "false", "leakSensorId": ""}, False)
    assert plugin.debug is False
