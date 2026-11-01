#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    plugin.py
# Description: Water Leak Monitor - monitors water leak sensors and sends
#              Pushover + Email alerts with confirmation retests to avoid
#              false alarms.
# Author:      CliveS & Claude Fable 5.1 & Claude Opus 5.5
# Date:        01-11-2026
# Version:     1.11.0
#
# v1.11.0 (01-11-2026): fixes from the 1.10.0 deep review, so a real leak is
# harder to miss.
# * A sensor that has gone QUIET (no change in Indigo's lastChanged for
#   staleHours, default 12) counts as "not answering", the same as one in error.
#   A flat Zigbee battery usually just stops the reports, with no error shown.
# * Low-battery notice (default at 20%) from a battery state whose name is a
#   setting (default "batteryLevel", Indigo's standard). A device without that
#   state is skipped quietly.
# * A deleted or re-created sensor now sends the "not answering" phone/email
#   notice as well as the hourly Event Log error.
# * A "not answering" notice that reached nobody is retried every 5 minutes
#   instead of being counted as told.
# * A sensor that drops out while it reads WET sends an URGENT message (leak
#   priority and sound), retried every minute until it goes out.
# * Leak alerts: Pushover priority is a setting, default 2 (Emergency — the
#   Pushover plugin repeats it every 10 minutes for up to 24 hours until you
#   acknowledge it); sound is a setting, default "siren" (was "vibrate");
#   re-alert default is 15 minutes (was 0). A saved setting is not changed.
# * Changing the sensor ID clears the old sensor's "already alerted" latch, so
#   a new sensor that is already wet is alerted.
#
# v1.10.0 (27-09-2026, Claude Opus 5.5): a sensor in error or disabled is now
# reported once (WARNING + Pushover/email, at most one notice per 30 min) and
# again when it answers; no personal default sensor ID (blank = not configured,
# logged once at INFO); "Leak sensor not found" repeats at most hourly; the
# stale bundle CLAUDE.md is gone.
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
#   than rushed into this release.
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

# No default leak sensor: a blank Leak Sensor Device ID means "not configured".
# (Until v1.10.0 the default was the author's own device ID, which does not exist
# on anyone else's system and filled their log with "not found" errors.)
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
SENSOR_NOTICE_GAP   = 1800  # at most one "sensor not answering" notice per 30 min,
                            # so a sensor that drops in and out cannot flood the phone.
                            # A drop that outlasts the gap is still reported.
NOT_FOUND_LOG_GAP   = 3600  # repeat the "Leak sensor not found" error at most hourly
NOTICE_RETRY_BACKOFF = 300  # seconds before retrying a status notice that reached nobody
BATTERY_NOTICE_GAP  = 86400 # at most one low-battery notice per day
BATTERY_OK_MARGIN   = 10    # battery counts as replaced once this many % above the warning
                            # level, so a reading wobbling around it cannot flood the phone

# Defaults for the v1.11.0 settings (all can be changed in Configure).
DEFAULT_REALERT_MINUTES   = 15
DEFAULT_STALE_HOURS       = 12
DEFAULT_BATTERY_STATE     = "batteryLevel"   # Indigo's standard battery state
DEFAULT_LOW_BATTERY_PCT   = 20
DEFAULT_PUSHOVER_SOUND    = "siren"
DEFAULT_PUSHOVER_PRIORITY = "2"              # Emergency: repeats until acknowledged
PUSHOVER_PRIORITIES       = ("1", "2")       # the leak alert is never below High


def _describe_duration(seconds):
    """How long, as a person would say it: 'a minute', '12 minutes', 'about 3 hours'."""
    minutes = int(round(max(0.0, seconds) / 60.0))
    if minutes < 1:
        return "less than a minute"
    if minutes == 1:
        return "a minute"
    if minutes < 90:
        return f"{minutes} minutes"
    return f"about {int(round(minutes / 60.0))} hours"


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug             = pluginPrefs.get("showDebugInfo", False)
        self.last_sensor_state = None
        self.alert_sent        = False   # True only once an alert has been DELIVERED
        self._alert_retry_at   = 0.0     # monotonic time of the next delivery retry
        self._realert_at       = 0.0     # monotonic time of the next re-alert (escalation)
        self.timestamp_enabled = bool(pluginPrefs.get("timestampEnabled", True))
        self._apply_settings(pluginPrefs)

        if install_timestamp_filter:
            self._ts_filter = install_timestamp_filter(self, enabled=self.timestamp_enabled)
        else:
            self._ts_filter = None

        self._init_watch_state()

        # Resolve config: IndigoSecrets first, then PluginConfig. A blank sensor
        # ID resolves to 0, which means "not configured" (no personal default).
        self._sensor_id_raw = pluginPrefs.get("leakSensorId", "")
        self.leak_sensor_id = _as_int(self._sensor_id_raw, 0)
        self.email_to       = _SECRETS_EMAIL or pluginPrefs.get("alertEmail", "")
        self.email_subject  = pluginPrefs.get("alertSubject", "") or DEFAULT_EMAIL_SUBJECT

        if not self.email_to:
            self.logger.error(
                "No alert email configured. Set WATERLEAK_ALERT_EMAIL in IndigoSecrets.py "
                "OR fill in the Alert Email field via Plugins -> Water Leak Monitor -> Configure."
            )

        # Startup banner moved to showPluginInfo on demand (revised 25-May-2026 per Jay).

    def _init_watch_state(self):
        """Sensor-watch bookkeeping: offline notices (v1.10.0), not-found rate
        limit, the once-only "not configured" note, and (v1.11.0) the wet-drop
        and low-battery notices."""
        self._offline_since       = None    # monotonic time the sensor went unavailable
        self._offline_notified    = False   # user told it is down, not yet told it is back
        self._offline_notice_next = 0.0     # earliest monotonic time for another down notice
        self._sensor_missing      = False
        self._missing_log_next    = 0.0
        self._config_note_logged  = False
        self._last_sensor_name    = ""      # remembered so a deleted sensor can be named
        self._wet_drop_pending    = False   # sensor dropped out while WET, urgent notice owed
        self._wet_drop_retry_at   = 0.0
        self._battery_low         = False
        self._battery_notice_next = 0.0

    def _apply_settings(self, prefs):
        """Read the alert and sensor-health settings from pluginPrefs or the
        Configure dialog. A setting never saved takes its default; a box the
        user cleared takes the default too, except Battery State Name, where
        blank means "do not check the battery"."""
        self.realert_minutes   = max(0, _as_int(prefs.get("reAlertMinutes"), DEFAULT_REALERT_MINUTES))
        self.stale_hours       = max(0, _as_int(prefs.get("staleHours"), DEFAULT_STALE_HOURS))
        self.low_battery_pct   = min(100, max(0, _as_int(prefs.get("lowBatteryPercent"), DEFAULT_LOW_BATTERY_PCT)))
        raw_state              = prefs.get("batteryStateName")
        self.battery_state     = DEFAULT_BATTERY_STATE if raw_state is None else str(raw_state).strip()
        self.pushover_sound    = str(prefs.get("pushoverSound") or "").strip() or DEFAULT_PUSHOVER_SOUND
        priority               = str(prefs.get("pushoverPriority") or "").strip()
        self.pushover_priority = priority if priority in PUSHOVER_PRIORITIES else DEFAULT_PUSHOVER_PRIORITY

    def startup(self):
        self.logger.info(f"Water Leak Monitor started — sensor ID: {self.leak_sensor_id or '(none chosen)'}")
        self.logger.info(f"Poll interval: {POLL_INTERVAL}s | Retests: {QUICK_RETEST_COUNT} x {QUICK_RETEST_DELAY}s")
        self.logger.info(f"Alert email: {self.email_to or '(not set)'}")
        realert_text = f"{self.realert_minutes} min" if self.realert_minutes > 0 else "off"
        quiet_text   = f"{self.stale_hours} h" if self.stale_hours > 0 else "off"
        self.logger.info(
            f"Re-alert: {realert_text} | Pushover priority {self.pushover_priority} | "
            f"Quiet alarm: {quiet_text}"
        )

    def shutdown(self):
        self.logger.info("Water Leak Monitor stopped")

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if userCancelled:
            return
        self.debug           = valuesDict.get("showDebugInfo", False)
        new_sensor_id        = _as_int(valuesDict.get("leakSensorId"), 0)
        if new_sensor_id != self.leak_sensor_id:
            # A different sensor: forget everything about the old one, including
            # its "already alerted" latch — otherwise a new sensor that is
            # already wet would never be alerted (v1.11.0).
            self._init_watch_state()
            self.alert_sent        = False
            self.last_sensor_state = None
            self._alert_retry_at   = 0.0
            self._realert_at       = 0.0
        self._sensor_id_raw      = valuesDict.get("leakSensorId", "")
        self.leak_sensor_id      = new_sensor_id
        self._sensor_missing     = False
        self._missing_log_next   = 0.0
        self._config_note_logged = False
        self.email_to        = _SECRETS_EMAIL or valuesDict.get("alertEmail", "")
        self.email_subject   = valuesDict.get("alertSubject", "") or DEFAULT_EMAIL_SUBJECT
        self._apply_settings(valuesDict)
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

    @staticmethod
    def _unavailable_reason(sensor):
        """Why the sensor cannot be read, or "" if it can: Indigo's error text
        for a device that has stopped answering, or "disabled"."""
        err = getattr(sensor, "errorState", None)
        if err:
            return str(err)
        if getattr(sensor, "enabled", True) is False:
            return "disabled"
        return ""

    def _note_unconfigured(self):
        """No usable sensor ID: say so ONCE (per start or settings save)."""
        if self._config_note_logged:
            return
        self._config_note_logged = True
        raw = str(self._sensor_id_raw or "").strip()
        if raw:
            self.logger.warning(
                f"Leak Sensor Device ID '{raw}' is not a number, so no leak sensor is being "
                f"watched. Paste the sensor's ID in Plugins -> Water Leak Monitor -> Configure."
            )
        else:
            self.logger.info(
                "No leak sensor chosen yet, so nothing is being watched. Paste the sensor's ID "
                "into Leak Sensor Device ID in Plugins -> Water Leak Monitor -> Configure."
            )

    def _quiet_reason(self, sensor):
        """v1.11.0: "" unless the sensor has gone quiet — Indigo's lastChanged
        is older than stale_hours. A flat Zigbee battery usually just stops the
        reports, leaving the last ("dry") state and no error. Off when
        stale_hours is 0; skipped quietly if lastChanged is missing or is not
        a date/time this code can compare."""
        if self.stale_hours <= 0:
            return ""
        last = getattr(sensor, "lastChanged", None)
        if not isinstance(last, datetime):
            return ""
        try:
            age = (datetime.now() - last).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return ""   # e.g. a timezone-aware value; never let this check break the tick
        if age < self.stale_hours * 3600:
            return ""
        return f"no change reported for {_describe_duration(age)}"

    def _check_battery(self, sensor):
        """v1.11.0: a status notice when the battery state is at or below
        low_battery_pct — at most one a day, retried if it reached nobody.
        Skipped quietly when the check is off, the device has no state of that
        name, or the value is not a number."""
        if self.low_battery_pct <= 0 or not self.battery_state:
            return
        try:
            states = sensor.states
            if self.battery_state not in states:
                return
            level = float(str(states.get(self.battery_state)).strip())
        except (TypeError, ValueError, AttributeError):
            return
        if level != level:   # NaN
            return
        if level > self.low_battery_pct:
            if self._battery_low and level >= self.low_battery_pct + BATTERY_OK_MARGIN:
                self._battery_low         = False
                self._battery_notice_next = 0.0
                self.logger.info(f"Leak sensor '{sensor.name}' battery is at {level:.0f}% — OK again")
            return
        now = _time.monotonic()
        if not self._battery_low:
            self._battery_low = True
            self.logger.warning(
                f"Leak sensor '{sensor.name}' battery is low ({level:.0f}%) — replace it soon"
            )
        if now < self._battery_notice_next:
            return
        sent = self._send_status_notice(
            "Leak sensor battery low",
            f"The battery in {sensor.name} is at {level:.0f} percent. Replace it soon: when it "
            f"runs flat the sensor goes quiet and cannot report a leak.",
        )
        self._battery_notice_next = now + (BATTERY_NOTICE_GAP if sent else NOTICE_RETRY_BACKOFF)

    def _note_sensor_missing(self):
        """The configured ID matches no device (deleted, or re-created with a
        new ID). Rate-limited ERROR in the log, and (v1.11.0) the same phone/
        email "not answering" notice as a sensor in error."""
        self._sensor_missing = True
        now = _time.monotonic()
        if now >= self._missing_log_next:
            self._missing_log_next = now + NOT_FOUND_LOG_GAP
            self.logger.error(
                f"Leak sensor not found (ID: {self.leak_sensor_id}) — nothing is being watched. "
                f"Check Leak Sensor Device ID in Configure. (Repeats hourly until fixed.)"
            )
        name = self._last_sensor_name or f"The leak sensor (ID {self.leak_sensor_id})"
        self._handle_unavailable(
            name, f"Indigo has no device with ID {self.leak_sensor_id}, so it may have been deleted or re-created"
        )

    def _handle_unavailable(self, name, reason):
        """The sensor cannot be read (error, disabled, quiet or missing):
        drop the leak latch, tell the user, and if its last reading was WET
        owe them an urgent message."""
        if self.last_sensor_state:
            self._wet_drop_pending  = True
            self._wet_drop_retry_at = 0.0
        if self.alert_sent or self.last_sensor_state:
            self.logger.debug("Sensor unavailable — resetting leak state")
        self.alert_sent        = False
        self.last_sensor_state = None
        self._note_sensor_unavailable(name, reason)
        self._send_wet_drop_notice(name, reason)

    def _send_wet_drop_notice(self, name, reason):
        """v1.11.0: the sensor read WET and then stopped answering. Send an
        urgent message (leak priority and sound); retry every
        ALERT_RETRY_BACKOFF until it goes out or the sensor is back."""
        now = _time.monotonic()
        if not self._wet_drop_pending or now < self._wet_drop_retry_at:
            return
        self.logger.error(
            f"[!] Leak sensor '{name}' stopped answering while it read WET ({reason}) — "
            f"go and look"
        )
        sent = self._send_status_notice(
            "[URGENT] Leak sensor lost while WET",
            f"The last reading from {name} was WET, and it has now stopped answering "
            f"({reason}). Water Leak Monitor cannot tell whether water is still there. "
            f"Go and look.",
            urgent=True,
        )
        if sent:
            self._wet_drop_pending = False
        else:
            self._wet_drop_retry_at = now + ALERT_RETRY_BACKOFF
            self.logger.error(
                f"[!] Could not send the WET sensor message by email or Pushover — "
                f"retrying in {ALERT_RETRY_BACKOFF}s"
            )

    def _note_sensor_unavailable(self, name, reason):
        """The sensor cannot be read. Tell the user once (WARNING +
        Pushover/email), no more than once per SENSOR_NOTICE_GAP. A notice
        that reached nobody is retried after NOTICE_RETRY_BACKOFF (v1.11.0)
        instead of being counted as told."""
        now = _time.monotonic()
        if self._offline_since is None:
            self._offline_since = now
        if self._offline_notified or now < self._offline_notice_next:
            return
        self.logger.warning(
            f"Leak sensor '{name}' is not answering ({reason}) — a leak cannot be "
            f"seen until it is back"
        )
        sent = self._send_status_notice(
            "Leak sensor not answering",
            f"{name} has stopped answering, so Water Leak Monitor cannot see whether "
            f"it is wet ({reason}). You will get another message when it is back.",
        )
        if sent:
            self._offline_notified    = True
            self._offline_notice_next = now + SENSOR_NOTICE_GAP
        else:
            self._offline_notice_next = now + NOTICE_RETRY_BACKOFF
            self.logger.warning(
                f"The 'not answering' message could not be sent by email or Pushover — "
                f"trying again in {NOTICE_RETRY_BACKOFF // 60} minutes"
            )

    def _note_sensor_back(self, name):
        """The sensor answers again after being unavailable. If the user was
        told it was down, tell them it is back (INFO + Pushover/email)."""
        self._wet_drop_pending = False
        if self._offline_since is None:
            return
        away = _time.monotonic() - self._offline_since
        self._offline_since = None
        if not self._offline_notified:
            self.logger.debug(f"Leak sensor '{name}' answered again after a short drop")
            return
        self._offline_notified = False
        self.logger.info(f"Leak sensor '{name}' is answering again — watching resumed")
        self._send_status_notice(
            "Leak sensor back",
            f"{name} is answering again after {_describe_duration(away)}, and "
            f"Water Leak Monitor is watching it once more.",
        )

    def _check_leak_sensor(self):
        """Check sensor state; confirm + alert on a leak, retrying delivery if
        a confirmed alert could not be sent."""
        if not self.leak_sensor_id:
            self._note_unconfigured()
            return
        try:
            sensor = indigo.devices[self.leak_sensor_id]
        except KeyError:
            self._note_sensor_missing()
            return
        if self._sensor_missing:
            self._sensor_missing   = False
            self._missing_log_next = 0.0
            self.logger.info(f"Leak sensor found again (ID: {self.leak_sensor_id}) — watching resumed")
        self._last_sensor_name = sensor.name

        reason = self._unavailable_reason(sensor) or self._quiet_reason(sensor)
        if reason:
            self._handle_unavailable(sensor.name, reason)
            return
        self._note_sensor_back(sensor.name)
        self._check_battery(sensor)

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
                "msgPriority": self.pushover_priority,
                "msgSound":    self.pushover_sound,
            })
            self.logger.info("[OK] Pushover alert sent")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to send Pushover alert: {exc}")
            return False

    def _send_status_notice(self, title, body, urgent=False):
        """Send a sensor-status notice: email + Pushover. Normal priority and
        vibrate, unless urgent (v1.11.0: the sensor dropped out while WET),
        which uses the leak alert's priority and sound. Returns True if at
        least one channel accepted it."""
        email_ok = False
        if self.email_to:
            try:
                indigo.server.sendEmailTo(self.email_to, subject=f"Water Leak Monitor: {title}", body=body)
                email_ok = True
            except Exception as exc:
                self.logger.error(f"Failed to send sensor status email: {exc}")
        push_ok = False
        try:
            pushover = indigo.server.getPlugin(PUSHOVER_PLUGIN_ID)
            if pushover is not None and pushover.isEnabled():
                pushover.executeAction("send", props={
                    "msgTitle":    title,
                    "msgBody":     body,
                    "msgPriority": self.pushover_priority if urgent else "0",
                    "msgSound":    self.pushover_sound if urgent else "vibrate",
                })
                push_ok = True
        except Exception as exc:
            self.logger.error(f"Failed to send sensor status Pushover message: {exc}")
        if not (email_ok or push_ok):
            self.logger.warning(f"Sensor status message '{title}' reached nobody (no email or Pushover worked)")
        return email_ok or push_ok

    # ----------------------------------------------------------------
    # Menu handlers
    # ----------------------------------------------------------------

    def sendTestAlert(self, valuesDict=None, typeId=None):
        """Menu: Send Test Alert — fires the Pushover + email path so the user
        can confirm delivery works WITHOUT waiting for a real leak."""
        try:
            name = indigo.devices[self.leak_sensor_id].name if self.leak_sensor_id else "your leak sensor"
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
        if not self.leak_sensor_id:
            sensor_line = "none chosen yet"
        else:
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
            ("Pushover alert:",    f"priority {self.pushover_priority}, sound '{self.pushover_sound}'"),
            ("Quiet alarm after:", f"{self.stale_hours} h" if self.stale_hours > 0 else "off"),
            ("Low battery at:",    f"{self.low_battery_pct}% of '{self.battery_state}'"
                                   if self.low_battery_pct > 0 and self.battery_state else "off"),
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
