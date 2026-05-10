#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    plugin.py
# Description: Water Leak Monitor - monitors water leak sensors and sends
#              Pushover + Email alerts with confirmation retests to avoid
#              false alarms.
# Author:      CliveS & Claude Sonnet 4.6
# Date:        09-04-2026
# Version:     1.4

import indigo
import os as _os
import sys as _sys
from datetime import datetime

_sys.path.insert(0, _os.getcwd())
try:
    from plugin_utils import log_startup_banner
except ImportError:
    log_startup_banner = None

_sys.path.insert(0, "/Library/Application Support/Perceptive Automation")
try:
    from IndigoSecrets import PUSHOVER_USER_TOKEN
except ImportError:
    PUSHOVER_USER_TOKEN = ""   # Falls back to hardcoded value below if missing

# ================================
# CONFIGURATION
# ================================

LEAK_SENSOR_ID      = 5913615   # "Bathroom Boiler Leak Sensor"

EMAIL_TO            = "boiler-leak-alert@strudwick.co.uk"
EMAIL_SUBJECT       = "[URGENT ALERT] Bathroom Boiler Water Leak Detected"

PUSHOVER_PLUGIN_ID  = "io.thechad.indigoplugin.pushover"

POLL_INTERVAL       = 2.0   # seconds between sensor checks
QUICK_RETEST_DELAY  = 5     # seconds before confirmation retest
QUICK_RETEST_COUNT  = 1     # single retest (1 x 5s = 5s confirmation window)


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug            = pluginPrefs.get("showDebugInfo", False)
        self.last_sensor_state = None
        self.alert_sent       = False

        if log_startup_banner:
            log_startup_banner(pluginId, pluginDisplayName, pluginVersion)
        else:
            indigo.server.log(f"{pluginDisplayName} v{pluginVersion} starting")

    def startup(self):
        self.logger.info(f"Water Leak Monitor started — sensor ID: {LEAK_SENSOR_ID}")
        self.logger.info(f"Poll interval: {POLL_INTERVAL}s | Retests: {QUICK_RETEST_COUNT} x {QUICK_RETEST_DELAY}s")

    def shutdown(self):
        self.logger.info("Water Leak Monitor stopped")

    def runConcurrentThread(self):
        try:
            while True:
                self._check_leak_sensor()
                self.sleep(POLL_INTERVAL)
        except self.StopThread:
            pass

    # ----------------------------------------------------------------
    # Sensor monitoring
    # ----------------------------------------------------------------

    def _check_leak_sensor(self):
        """Check sensor state and trigger confirmation if leak detected."""
        try:
            sensor = indigo.devices[LEAK_SENSOR_ID]
        except KeyError:
            self.logger.error(f"Leak sensor not found (ID: {LEAK_SENSOR_ID})")
            return

        if hasattr(sensor, "errorState") and sensor.errorState:
            if self.alert_sent:
                self.logger.debug("Sensor unavailable — resetting alert flag")
                self.alert_sent = False
            return

        current_state = sensor.states.get("waterLeak", False)

        if current_state and not self.last_sensor_state and not self.alert_sent:
            self.logger.warning("[!] LEAK DETECTED — starting confirmation process")
            self._confirm_and_alert()
        elif not current_state and self.last_sensor_state:
            self.logger.info("Leak sensor cleared")
            self.alert_sent = False

        self.last_sensor_state = current_state

    def _quick_confirm_leak(self):
        """Retest sensor QUICK_RETEST_COUNT times to rule out false alarms."""
        self.logger.info(f"Performing {QUICK_RETEST_COUNT} confirmation retests...")

        for test_num in range(1, QUICK_RETEST_COUNT + 1):
            self.logger.info(f"Retest {test_num}/{QUICK_RETEST_COUNT} in {QUICK_RETEST_DELAY}s...")
            self.sleep(QUICK_RETEST_DELAY)

            try:
                sensor = indigo.devices[LEAK_SENSOR_ID]
                if hasattr(sensor, "errorState") and sensor.errorState:
                    self.logger.info(f"Sensor unavailable on retest {test_num} — cancelling")
                    return False
                if not sensor.states.get("waterLeak", False):
                    self.logger.info(f"Leak cleared on retest {test_num} — false alarm")
                    return False
            except Exception as exc:
                self.logger.error(f"Error during retest {test_num}: {exc}")
                return False

        self.logger.error("[!] LEAK CONFIRMED after retests — sending alerts")
        return True

    def _confirm_and_alert(self):
        """Run confirmation retests then send alerts if still triggered."""
        if self._quick_confirm_leak():
            self._send_alerts()
            self.alert_sent = True

    # ----------------------------------------------------------------
    # Alerting
    # ----------------------------------------------------------------

    def _send_alerts(self):
        """Send Email+ and Pushover alerts."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._send_email(timestamp)
        self._send_pushover(timestamp)

    def _send_email(self, timestamp):
        """Send alert via indigo.server.sendEmailTo (uses first SMTP device)."""
        try:
            body = (
                f"LEAK DETECTED at Bathroom Boiler\n"
                f"Time: {timestamp}\n"
                f"Status: ACTIVE"
            )
            indigo.server.sendEmailTo(EMAIL_TO, subject=EMAIL_SUBJECT, body=body)
            self.logger.info("[OK] Email alert sent")
        except Exception as exc:
            self.logger.error(f"Failed to send email: {exc}")

    def _send_pushover(self, timestamp):
        """Send alert via Pushover plugin."""
        try:
            pushover = indigo.server.getPlugin(PUSHOVER_PLUGIN_ID)
            if not pushover.isEnabled():
                self.logger.warning("Pushover plugin not enabled — skipping push alert")
                return
            pushover.executeAction("send", props={
                "msgTitle":    "[URGENT] Water Leak",
                "msgBody":     f"LEAK DETECTED at Bathroom Boiler\nTime: {timestamp}",
                "msgPriority": "1",
                "msgSound":    "vibrate",
            })
            self.logger.info("[OK] Pushover alert sent")
        except Exception as exc:
            self.logger.error(f"Failed to send Pushover alert: {exc}")

    # ----------------------------------------------------------------
    # Menu handlers
    # ----------------------------------------------------------------

    def showPluginInfo(self, valuesDict=None, typeId=None):
        if log_startup_banner:
            log_startup_banner(self.pluginId, self.pluginDisplayName, self.pluginVersion)
        else:
            indigo.server.log(f"{self.pluginDisplayName} v{self.pluginVersion}")
