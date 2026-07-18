#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_plugin.py
# Description: Mock test suite for Water Leak Monitor — the first tests for this
#              SAFETY-CRITICAL plugin. Drives the leak state machine against a
#              stubbed indigo + a fake sensor, with NO Indigo runtime.
# Author:      CliveS & Claude Opus 4.8
# Date:        18-07-2026
# Version:     1.0
#
# Run:  python3 -m pytest test_plugin.py -q

import os
import sys
import types
import unittest
from unittest.mock import MagicMock

# --- stub indigo BEFORE importing plugin.py ---
_ind = types.ModuleType("indigo")


class _PB:
    def __init__(self, *a, **k):
        pass

    class StopThread(Exception):
        pass


_ind.PluginBase = _PB
_ind.Dict = dict
_ind.devices = {}
_ind.server = MagicMock()
sys.modules["indigo"] = _ind

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import plugin as wlm   # noqa: E402


class FakeSensor:
    def __init__(self, name="Bathroom Boiler Leak Sensor", states=None, error=None):
        self.name = name
        self.errorState = error
        self.states = states if states is not None else {"waterLeak": False}
        self._on = states.get("onOffState") if states else False

    @property
    def onState(self):
        return self._on


def make_plugin(email="x@example.com", realert_minutes=0):
    p = wlm.Plugin.__new__(wlm.Plugin)
    p.logger = MagicMock()
    p.debug = False
    p.last_sensor_state = False
    p.alert_sent = False
    p._alert_retry_at = 0.0
    p._realert_at = 0.0
    p.realert_minutes = realert_minutes
    p.leak_sensor_id = wlm.DEFAULT_LEAK_SENSOR_ID
    p.email_to = email
    p.email_subject = "leak"
    p.sleep = lambda _s: None
    return p


def _reset_server():
    _ind.server.reset_mock(return_value=True, side_effect=True)
    _ind.server.sendEmailTo.side_effect = None
    # Pushover disabled by default -> only email is the working channel unless a
    # test enables it.
    po = MagicMock()
    po.isEnabled.return_value = False
    _ind.server.getPlugin.return_value = po


class TestAsInt(unittest.TestCase):
    def test_coercion(self):
        self.assertEqual(wlm._as_int("42", 5), 42)
        self.assertEqual(wlm._as_int("", 5), 5)
        self.assertEqual(wlm._as_int("abc", 5), 5)
        self.assertEqual(wlm._as_int(None, 5), 5)
        self.assertEqual(wlm._as_int("  7 ", 5), 7)


class TestLeakStateKey(unittest.TestCase):
    """v1.8: read waterLeak, else fall back to onOffState/onState so Z-Wave
    sensors (no waterLeak state) are monitored too."""

    def setUp(self):
        _reset_server()
        self.p = make_plugin()

    def test_waterleak_key_used_when_present(self):
        s = FakeSensor(states={"waterLeak": True, "onOffState": False})
        self.assertTrue(self.p._leak_state(s))

    def test_onoffstate_fallback_when_no_waterleak(self):
        s = FakeSensor(states={"onOffState": True})   # Z-Wave: no waterLeak key
        self.assertTrue(self.p._leak_state(s))

    def test_clear(self):
        s = FakeSensor(states={"onOffState": False})
        self.assertFalse(self.p._leak_state(s))


class TestAlertDeliveryLatch(unittest.TestCase):
    """v1.8 CRITICAL regression: alert_sent latches only on a real delivery; a
    confirmed leak whose channels fail is retried, not silently dropped."""

    def setUp(self):
        _reset_server()
        wlm.QUICK_RETEST_DELAY = 0
        wlm.ALERT_RETRY_BACKOFF = 0
        self.sensor = FakeSensor(states={"waterLeak": True})
        _ind.devices[wlm.DEFAULT_LEAK_SENSOR_ID] = self.sensor
        self.p = make_plugin()

    def _enable_pushover(self, ok=True):
        po = MagicMock()
        po.isEnabled.return_value = True
        if not ok:
            po.executeAction.side_effect = RuntimeError("pushover fail")
        _ind.server.getPlugin.return_value = po

    def test_total_delivery_failure_not_latched(self):
        _ind.server.sendEmailTo.side_effect = RuntimeError("SMTP down")
        self._enable_pushover(ok=False)
        self.p._check_leak_sensor()
        self.assertFalse(self.p.alert_sent, "must NOT latch when nothing was delivered")

    def test_retries_while_leak_persists_then_latches_on_recovery(self):
        _ind.server.sendEmailTo.side_effect = RuntimeError("SMTP down")
        self._enable_pushover(ok=False)
        self.p._check_leak_sensor()
        n0 = _ind.server.sendEmailTo.call_count
        self.p._check_leak_sensor()
        self.assertGreater(_ind.server.sendEmailTo.call_count, n0, "should retry delivery")
        # email recovers
        _ind.server.sendEmailTo.side_effect = None
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent, "latches once an alert is delivered")
        n1 = _ind.server.sendEmailTo.call_count
        self.p._check_leak_sensor()
        self.assertEqual(_ind.server.sendEmailTo.call_count, n1, "no repeat sends after delivered")

    def test_email_success_latches_immediately(self):
        # email works, pushover disabled -> one channel delivered
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent)
        _ind.server.sendEmailTo.assert_called()

    def test_alert_uses_sensor_name_not_hardcoded(self):
        self.sensor.name = "Kitchen Under Sink Water Sensor"
        self.p._check_leak_sensor()
        body = _ind.server.sendEmailTo.call_args.kwargs.get("body", "")
        self.assertIn("Kitchen Under Sink Water Sensor", body)
        self.assertNotIn("Bathroom Boiler", body)


class TestStateMachine(unittest.TestCase):
    """Rising-edge detection, latch clear on sensor-clear and errorState."""

    def setUp(self):
        _reset_server()
        wlm.QUICK_RETEST_DELAY = 0
        wlm.ALERT_RETRY_BACKOFF = 0
        self.sensor = FakeSensor(states={"waterLeak": False})
        _ind.devices[wlm.DEFAULT_LEAK_SENSOR_ID] = self.sensor
        self.p = make_plugin()

    def test_no_alert_when_clear(self):
        self.p._check_leak_sensor()
        _ind.server.sendEmailTo.assert_not_called()
        self.assertFalse(self.p.alert_sent)

    def test_alert_fires_once_not_every_tick(self):
        self.sensor.states["waterLeak"] = True
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent)
        n = _ind.server.sendEmailTo.call_count
        self.p._check_leak_sensor()
        self.p._check_leak_sensor()
        self.assertEqual(_ind.server.sendEmailTo.call_count, n, "must not re-alert every tick")

    def test_latch_clears_on_sensor_clear(self):
        self.sensor.states["waterLeak"] = True
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent)
        self.sensor.states["waterLeak"] = False
        self.p._check_leak_sensor()
        self.assertFalse(self.p.alert_sent)

    def test_latch_clears_on_errorstate(self):
        self.sensor.states["waterLeak"] = True
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent)
        self.sensor.errorState = "no ack"
        self.p._check_leak_sensor()
        self.assertFalse(self.p.alert_sent)

    def test_false_alarm_cancels_and_rearms(self):
        # leak appears, but clears during the retest -> false alarm, no latch,
        # and a genuine later leak still fires.
        self.sensor.states["waterLeak"] = True
        orig = self.p._quick_confirm_leak
        self.p._quick_confirm_leak = lambda: False   # simulate retest = false alarm
        self.p._check_leak_sensor()
        self.assertFalse(self.p.alert_sent)
        _ind.server.sendEmailTo.assert_not_called()
        # now a real, confirmed leak
        self.p._quick_confirm_leak = orig
        self.p._check_leak_sensor()
        self.assertTrue(self.p.alert_sent)


class TestReAlertEscalation(unittest.TestCase):
    """v1.9: with reAlertMinutes>0, a persisting leak re-alerts on schedule;
    with 0 (default) it alerts once only."""

    def setUp(self):
        _reset_server()
        wlm.QUICK_RETEST_DELAY = 0
        wlm.ALERT_RETRY_BACKOFF = 0
        self.sensor = FakeSensor(states={"waterLeak": True})
        _ind.devices[wlm.DEFAULT_LEAK_SENSOR_ID] = self.sensor

    def test_realert_off_alerts_once(self):
        p = make_plugin(realert_minutes=0)
        p._check_leak_sensor()
        n = _ind.server.sendEmailTo.call_count
        p._check_leak_sensor()
        p._check_leak_sensor()
        self.assertEqual(_ind.server.sendEmailTo.call_count, n)

    def test_realert_on_resends_after_interval(self):
        p = make_plugin(realert_minutes=5)   # _realert_at set 300s ahead on latch
        p._check_leak_sensor()
        self.assertTrue(p.alert_sent)
        n = _ind.server.sendEmailTo.call_count
        p._check_leak_sensor()   # not yet due
        self.assertEqual(_ind.server.sendEmailTo.call_count, n)
        # force the re-alert time to now
        p._realert_at = 0.0
        p._check_leak_sensor()
        self.assertGreater(_ind.server.sendEmailTo.call_count, n, "should re-alert once due")


class TestSendTestAlert(unittest.TestCase):
    """v1.9: the Test Alert menu exercises the delivery path with a TEST label."""

    def setUp(self):
        _reset_server()
        self.sensor = FakeSensor(name="Kitchen Under Sink Water Sensor",
                                 states={"onOffState": False})
        _ind.devices[wlm.DEFAULT_LEAK_SENSOR_ID] = self.sensor

    def test_test_alert_sends_with_test_label(self):
        p = make_plugin()
        p.sendTestAlert()
        body = _ind.server.sendEmailTo.call_args.kwargs.get("body", "")
        self.assertIn("Kitchen Under Sink Water Sensor (TEST)", body)


class TestTickIsolation(unittest.TestCase):
    """v1.8: an exception in a tick must not kill the monitor loop."""

    def test_tick_exception_logged_not_fatal(self):
        _reset_server()
        p = make_plugin()
        calls = {"n": 0}

        def _boom():
            calls["n"] += 1
            raise ValueError("boom")
        p._check_leak_sensor = _boom

        def _sleep(_s):
            if calls["n"] >= 2:
                raise wlm.Plugin.StopThread()
        p.sleep = _sleep
        p.StopThread = wlm.Plugin.StopThread
        p.runConcurrentThread()   # must return cleanly, not raise ValueError
        self.assertGreaterEqual(calls["n"], 2)
        p.logger.error.assert_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
