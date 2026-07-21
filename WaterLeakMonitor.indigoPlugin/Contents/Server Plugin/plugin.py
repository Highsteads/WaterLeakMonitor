#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    plugin.py
# Description: Water Leak Monitor - monitors water leak sensors and sends
#              Pushover + Email alerts with confirmation retests to avoid
#              false alarms.
# Author:      CliveS & Claude Opus 4.8
# Date:        21-07-2026
# Version:     1.9.1
#
# v1.9.1 (21-07-2026): shared plugin_utils.py refreshed to v1.3 — the
# estate-wide propagation of the four Appliance Monitor deep-review fixes.
# * install_timestamp_filter() is idempotent — a second call used to stack a
#   second filter, so every log line came out with two timestamps.
# * `import indigo` is soft, so the module imports outside the Indigo host and
#   can be exercised by offline tests.
# * A malformed log call keeps its arguments in the log instead of dropping
#   them, so a %-placeholder mismatch is visible.
# * New shared as_bool() — a pref re-serialised as the string "false" is
#   truthy, which is exactly the wrong answer.
#
# v1.9 (18-07-2026) — deep-review IMPROVEMENTS batch:
# - New "Send Test Alert" menu item — fires the Pushover + email path with a
#   TEST label so users can confirm delivery works without a real leak.
# - Optional re-alert escalation: a new "Re-alert every (minutes)" config
#   (default 0 = off) re-sends the alert while a confirmed leak keeps flowing,
#   so a persisting flood keeps nagging.
# - Show Plugin Info now reports the monitored sensor, its resolved leak state
#   key, the alert email and the re-alert setting.
# - DEFAULT_EMAIL_SUBJECT + the PluginConfig subject default no longer name
#   "Bathroom Boiler" (the alert body already uses the real sensor name).
# - Declined/deferred: monitoring MULTIPLE leak sensors at once — a valuable
#   feature but a structural change to the (now safety-hardened + tested) state
#   machine and the config contract, so planned as its own focused batch rather
#   than rushed into this release. See repo CLAUDE.md.
#
# v1.8 (18-07-2026) — deep-review SAFETY-FIX batch:
# - CRITICAL: a CONFIRMED leak whose alert could not be delivered is no longer
#   silently latched as "alerted". _send_email / _send_pushover now return a
#   delivery-success bool, _send_alerts returns True only if at least one
#   channel delivered, and alert_sent latches only on that success. A confirmed
#   leak with a mail/Pushover outage keeps retrying (bounded back-off,
#   ALERT_RETRY_BACKOFF) and logs a loud ERROR, so a real leak is never dropped.
# - The runConcurrentThread tick body is fully isolated: an unexpected exception
#   is logged and the loop continues (previously only the device lookup was
#   guarded, so a stray error would silently stop leak monitoring for good).
# - The confirmation retest no longer permanently misses a leak that flickers
#   clear during the 5s window — while the sensor still reads active and no
#   alert has been delivered, it re-confirms and re-attempts.
# - New _leak_state reader: prefers the Zigbee2MQTT "waterLeak" state but falls
#   back to the native onOffState, so Z-Wave (and other) leak sensors that
#   expose only onOffState are monitored too (they were silently unwatched).
# - Alert body + Pushover message now name the ACTUAL configured sensor instead
#   of the hardcoded "Bathroom Boiler".
# - First-ever test suite: test_plugin.py, 14 tests.
#
# v1.6 (23-05-2026):
# - Add millisecond timestamp prefix [HH:MM:SS.mmm] on every log line, matching
#   Device Activity Monitor convention. Driven by a MillisecondTimestampFilter
#   installed on self.logger via plugin_utils.install_timestamp_filter().
# - New menu item "Toggle Timestamps in Log (on/off)" — flips the
#   timestampEnabled pluginPref live. Default ON so existing installs are
#   unchanged in feel but gain millisecond precision.
# - showPluginInfo now reports Timestamps state alongside the standard banner.
#
# v1.5 (13-05-2026):
# - Alert email moved to IndigoSecrets.py (WATERLEAK_ALERT_EMAIL) with
#   PluginConfig fallback. No more hardcoded email address.
# - Leak sensor ID moved to PluginConfig (was a module constant — broke
#   plugin for anyone with a different sensor ID).
# - Drop unused PUSHOVER_USER_TOKEN import (msgUser is optional when only one
#   Pushover user is configured, and we never passed it anyway).
# - Add PluginConfig.xml so users can configure without editing source.

import indigo
import os as _os
import sys as _sys
import time as _time
from datetime import datetime

_sys.path.insert(0, _os.getcwd())
try:
    from plugin_utils import log_startup_banner
except ImportError:
    log_startup_banner = None
try:
    from plugin_utils import install_timestamp_filter
except ImportError:
    install_timestamp_filter = None

_sys.path.insert(0, "/Library/Application Support/Perceptive Automation")
try:
    from IndigoSecrets import WATERLEAK_ALERT_EMAIL as _SECRETS_EMAIL
except ImportError:
    _SECRETS_EMAIL = ""

# ================================
# CONFIGURATION (defaults — overridden by PluginConfig / IndigoSecrets)
# ================================

DEFAULT_LEAK_SENSOR_ID = 5913615   # "Bathroom Boiler Leak Sensor"
DEFAULT_EMAIL_SUBJECT  = "[URGENT ALERT] Water Leak Detected"


def _as_int(value, default):
    """Coerce a config value to int, returning default on blank/non-numeric input."""
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default

PUSHOVER_PLUGIN_ID  = "io.thechad.indigoplugin.pushover"

POLL_INTERVAL       = 2.0   # seconds between sensor checks
QUICK_RETEST_DELAY  = 5     # seconds before confirmation retest
QUICK_RETEST_COUNT  = 1     # single retest (1 x 5s = 5s confirmation window)
ALERT_RETRY_BACKOFF = 60    # seconds between delivery retries when a CONFIRMED
                            # leak's alert could not be delivered (SMTP/Pushover
                            # down) — keep trying so a real leak is never silently
                            # dropped, without hammering the channels every tick.


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug             = pluginPrefs.get("showDebugInfo", False)
        self.last_sensor_state = None
        self.alert_sent        = False   # True only once an alert has been DELIVERED
        self._alert_retry_at   = 0.0     # monotonic time of the next delivery retry
        self._realert_at       = 0.0     # monotonic time of the next re-alert (escalation)
        self.realert_minutes   = _as_int(pluginPrefs.get("reAlertMinutes"), 0)
        self.timestamp_enabled = bool(pluginPrefs.get("timestampEnabled", True))

        if install_timestamp_filter:
            self._ts_filter = install_timestamp_filter(self, enabled=self.timestamp_enabled)
        else:
            self._ts_filter = None

        # Resolve config: IndigoSecrets first, then PluginConfig, then default.
        self.leak_sensor_id = _as_int(pluginPrefs.get("leakSensorId"), DEFAULT_LEAK_SENSOR_ID)
        self.email_to       = _SECRETS_EMAIL or pluginPrefs.get("alertEmail", "")
        self.email_subject  = pluginPrefs.get("alertSubject", "") or DEFAULT_EMAIL_SUBJECT

        if not self.email_to:
            self.logger.error(
                "No alert email configured. Set WATERLEAK_ALERT_EMAIL in IndigoSecrets.py "
                "OR fill in the Alert Email field via Plugins -> Water Leak Monitor -> Configure."
            )

        # Startup banner moved to showPluginInfo on demand (revised 25-May-2026 per Jay).

    def startup(self):
        self.logger.info(f"Water Leak Monitor started — sensor ID: {self.leak_sensor_id}")
        self.logger.info(f"Poll interval: {POLL_INTERVAL}s | Retests: {QUICK_RETEST_COUNT} x {QUICK_RETEST_DELAY}s")
        self.logger.info(f"Alert email: {self.email_to or '(not set)'}")

    def shutdown(self):
        self.logger.info("Water Leak Monitor stopped")

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if userCancelled:
            return
        self.debug           = valuesDict.get("showDebugInfo", False)
        self.leak_sensor_id  = _as_int(valuesDict.get("leakSensorId"), DEFAULT_LEAK_SENSOR_ID)
        self.email_to        = _SECRETS_EMAIL or valuesDict.get("alertEmail", "")
        self.email_subject   = valuesDict.get("alertSubject", "") or DEFAULT_EMAIL_SUBJECT
        self.realert_minutes = _as_int(valuesDict.get("reAlertMinutes"), 0)
        self.logger.info("Plugin configuration updated")

    def runConcurrentThread(self):
        try:
            while True:
                # Isolate the whole tick: an unexpected exception must NOT kill
                # the monitor thread (that would stop leak detection silently).
                try:
                    self._check_leak_sensor()
                except self.StopThread:
                    raise
                except Exception as exc:
                    self.logger.error(f"Leak-check tick failed: {exc}", exc_info=True)
                self.sleep(POLL_INTERVAL)
        except self.StopThread:
            pass

    # ----------------------------------------------------------------
    # Sensor monitoring
    # ----------------------------------------------------------------

    def _leak_state(self, sensor):
        """Read the sensor's leak state. Prefers the Zigbee2MQTT 'waterLeak'
        state; falls back to the native onOffState so Z-Wave and other leak
        sensors (which expose only onOffState) are monitored too."""
        if "waterLeak" in sensor.states:
            return bool(sensor.states.get("waterLeak", False))
        return bool(getattr(sensor, "onState", sensor.states.get("onOffState", False)))

    def _check_leak_sensor(self):
        """Check sensor state; confirm + alert on a leak, retrying delivery if
        a confirmed alert could not be sent."""
        try:
            sensor = indigo.devices[self.leak_sensor_id]
        except KeyError:
            self.logger.error(f"Leak sensor not found (ID: {self.leak_sensor_id})")
            return

        if getattr(sensor, "errorState", None):
            if self.alert_sent or self.last_sensor_state:
                self.logger.debug("Sensor unavailable — resetting leak state")
            self.alert_sent        = False
            self.last_sensor_state = None
            return

        current_state = self._leak_state(sensor)

        if not current_state:
            if self.last_sensor_state:
                self.logger.info("Leak sensor cleared")
            self.alert_sent        = False
            self._alert_retry_at   = 0.0
            self.last_sensor_state = False
            return

        # Leak is currently active. Attempt to alert until an alert is actually
        # DELIVERED (alert_sent). This covers both first detection and retrying
        # a confirmed leak whose delivery failed — a real leak is never dropped.
        if not self.alert_sent and _time.monotonic() >= self._alert_retry_at:
            if not self.last_sensor_state:
                self.logger.warning("[!] LEAK DETECTED — starting confirmation process")
            if self._quick_confirm_leak():
                delivered = self._send_alerts(sensor.name)
                if delivered:
                    self.alert_sent  = True
                    self._realert_at = _time.monotonic() + self.realert_minutes * 60
                else:
                    # Confirmed leak, but nothing was delivered — keep trying.
                    self._alert_retry_at = _time.monotonic() + ALERT_RETRY_BACKOFF
                    self.logger.error(
                        f"[!] LEAK CONFIRMED but NO alert could be delivered — "
                        f"retrying in {ALERT_RETRY_BACKOFF}s"
                    )
            # If _quick_confirm_leak() was a false alarm we simply do not latch;
            # last_sensor_state below stays in step so a genuine re-trigger works.

        elif self.alert_sent and self.realert_minutes > 0 and _time.monotonic() >= self._realert_at:
            # Escalation: the leak is still active and was already alerted —
            # re-notify every reAlertMinutes so a persisting flood keeps nagging.
            self.logger.warning(f"[!] LEAK STILL ACTIVE — re-alerting ({sensor.name})")
            self._send_alerts(sensor.name)
            self._realert_at = _time.monotonic() + self.realert_minutes * 60

        self.last_sensor_state = current_state

    def _quick_confirm_leak(self):
        """Retest sensor QUICK_RETEST_COUNT times to rule out false alarms."""
        self.logger.info(f"Performing {QUICK_RETEST_COUNT} confirmation retests...")

        for test_num in range(1, QUICK_RETEST_COUNT + 1):
            self.logger.info(f"Retest {test_num}/{QUICK_RETEST_COUNT} in {QUICK_RETEST_DELAY}s...")
            self.sleep(QUICK_RETEST_DELAY)

            try:
                sensor = indigo.devices[self.leak_sensor_id]
                if getattr(sensor, "errorState", None):
                    self.logger.info(f"Sensor unavailable on retest {test_num} — cancelling")
                    return False
                if not self._leak_state(sensor):
                    self.logger.info(f"Leak cleared on retest {test_num} — false alarm")
                    return False
            except Exception as exc:
                self.logger.error(f"Error during retest {test_num}: {exc}")
                return False

        self.logger.error("[!] LEAK CONFIRMED after retests")
        return True

    # ----------------------------------------------------------------
    # Alerting
    # ----------------------------------------------------------------

    def _send_alerts(self, location):
        """Send Email+ and Pushover alerts. Returns True if AT LEAST ONE channel
        delivered, so the caller only latches the alert on a real delivery."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_ok = self._send_email(timestamp, location)
        push_ok  = self._send_pushover(timestamp, location)
        return email_ok or push_ok

    def _send_email(self, timestamp, location):
        """Send alert via indigo.server.sendEmailTo (uses first SMTP device).
        Returns True on success, False on any failure."""
        if not self.email_to:
            self.logger.error("Cannot send leak alert email — no recipient configured")
            return False
        try:
            body = (
                f"LEAK DETECTED at {location}\n"
                f"Time: {timestamp}\n"
                f"Status: ACTIVE"
            )
            indigo.server.sendEmailTo(self.email_to, subject=self.email_subject, body=body)
            self.logger.info("[OK] Email alert sent")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to send email: {exc}")
            return False

    def _send_pushover(self, timestamp, location):
        """Send alert via Pushover plugin. Returns True on success, False on any
        failure (plugin missing/disabled, or the send raised)."""
        try:
            pushover = indigo.server.getPlugin(PUSHOVER_PLUGIN_ID)
            if pushover is None or not pushover.isEnabled():
                self.logger.warning("Pushover plugin not available — skipping push alert")
                return False
            pushover.executeAction("send", props={
                "msgTitle":    "[URGENT] Water Leak",
                "msgBody":     f"LEAK DETECTED at {location}\nTime: {timestamp}",
                "msgPriority": "1",
                "msgSound":    "vibrate",
            })
            self.logger.info("[OK] Pushover alert sent")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to send Pushover alert: {exc}")
            return False

    # ----------------------------------------------------------------
    # Menu handlers
    # ----------------------------------------------------------------

    def sendTestAlert(self, valuesDict=None, typeId=None):
        """Menu: Send Test Alert — fires the Pushover + email path so the user
        can confirm delivery works WITHOUT waiting for a real leak."""
        try:
            name = indigo.devices[self.leak_sensor_id].name
        except KeyError:
            name = f"sensor {self.leak_sensor_id}"
        self.logger.info("Sending TEST leak alert (Pushover + email) ...")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_ok = self._send_email(ts, f"{name} (TEST)")
        push_ok  = self._send_pushover(ts, f"{name} (TEST)")
        if email_ok or push_ok:
            self.logger.info(f"[OK] Test alert delivered — email={email_ok} pushover={push_ok}")
        else:
            self.logger.error("Test alert FAILED on BOTH channels — check email + Pushover config")

    def showPluginInfo(self, valuesDict=None, typeId=None):
        try:
            sensor  = indigo.devices[self.leak_sensor_id]
            sk      = "waterLeak" if "waterLeak" in sensor.states else "onOffState"
            sensor_line = f"{sensor.name} (ID {self.leak_sensor_id}, state '{sk}')"
        except KeyError:
            sensor_line = f"ID {self.leak_sensor_id} — NOT FOUND"
        extras = [
            ("Monitored sensor:",  sensor_line),
            ("Alert email:",       self.email_to or "(not set)"),
            ("Re-alert every:",    f"{self.realert_minutes} min" if self.realert_minutes > 0 else "off"),
            ("Timestamps in Log:", "ON" if self.timestamp_enabled else "OFF"),
        ]
        if log_startup_banner:
            log_startup_banner(self.pluginId, self.pluginDisplayName, self.pluginVersion, extras=extras)
        else:
            indigo.server.log(f"{self.pluginDisplayName} v{self.pluginVersion}")
            for label, value in extras:
                indigo.server.log(f"  {label} {value}")

    def menuToggleTimestamps(self):
        self.timestamp_enabled = not self.timestamp_enabled
        self.pluginPrefs["timestampEnabled"] = self.timestamp_enabled
        if self._ts_filter:
            self._ts_filter.enabled = self.timestamp_enabled
        state = "ON" if self.timestamp_enabled else "OFF"
        indigo.server.log(f"[{self.pluginDisplayName}] Timestamps in Log -> {state}")
