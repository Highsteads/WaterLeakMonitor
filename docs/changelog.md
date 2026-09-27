---
title: Version history
nav_order: 8
---

# Version history

The newest version is at the top.

## 1.9.3 — 11 September 2026

The plugin carries a note of where its code lives on GitHub, the same way other Indigo plugins do. Nothing else changed.

## 1.9.2 — 7 September 2026

The settings window had been stretched wider than it could show, so the help text beside a setting was cut off part way through. The long help now sits in a paragraph of its own, which wraps. No setting or behaviour changed.

## 1.9.1 — 21 July 2026

A tidy-up of the code shared with my other plugins. A log line can no longer come out with the time printed twice.

## 1.9 — 18 July 2026

- **Send Test Alert** in the Plugins menu sends a Pushover message and an email marked TEST, so you can check both reach you without a real leak.
- **Re-alert every (minutes)** is a new setting that sends the alerts again while the sensor stays wet. It starts at nought, which means one alert per leak.
- **Show Plugin Info** also lists the sensor being watched, the alert email address and the repeat-alert setting.
- The starting email subject no longer names my own bathroom boiler.

## 1.8 — 18 July 2026

- **A confirmed leak is never treated as dealt with until an alert has gone out.** Before, a leak whose email and Pushover message both failed was counted as sent, and no alert ever arrived. Now the plugin tries again every minute while the sensor is wet.
- One unexpected error can no longer stop the plugin watching the sensor.
- A leak that read dry for a moment during the five-second check is no longer missed.
- Z-Wave and other sensors that show water as **on** are watched. Before, only Zigbee sensors with a water leak reading were.
- The alerts name your own sensor, rather than always saying Bathroom Boiler.

## 1.7 — 5 June 2026

Anything that is not a number in **Leak Sensor Device ID** no longer stops the plugin starting or the settings saving. The plugin goes back to its starting number instead.

## 1.6 — 23 May 2026

Every log line starts with the time to the thousandth of a second, with a menu item to turn that off.

## 1.5 — 13 May 2026

- The sensor and the alert email address are set in **Plugins → Water Leak Monitor → Configure**. Before, they were written into the plugin's code, so it only worked with my own sensor.
- The alert email address can be kept in the shared `IndigoSecrets.py` file.
- The plugin's identity inside Indigo changed with this version.

## 1.4 — 9 April 2026

The first version on GitHub. It watched one Zigbee leak sensor every two seconds, checked a second time five seconds later, and sent a Pushover message and an email.

Earlier versions are not recorded.
