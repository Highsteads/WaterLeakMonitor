---
title: Home
nav_order: 1
---

# Water Leak Monitor for Indigo

This plugin lets [Indigo](https://www.indigodomo.com) keep watch on a water leak sensor you already have, and tell you straight away when it finds water. The moment the sensor reads wet, the plugin waits five seconds and checks again, and if it is still wet it sends you a Pushover message on your phone and an email.

I use it on the leak sensor by the boiler in the bathroom, where a slow drip could go unseen for days.

The plugin adds no devices, actions or triggers of its own. You point it at your sensor once, in its settings, and it watches from then on.

## What it does for you

- **Checks your leak sensor every two seconds**, whether it is a Zigbee sensor, a Z-Wave sensor or another kind that Indigo shows as on when it is wet.
- **Checks a second time before it alerts**, five seconds later, so a sensor that reads wet for a moment and then dry again does not wake you for nothing.
- **Sends a Pushover message and an email** naming the sensor and the time. The Pushover message goes at high priority and makes the phone vibrate.
- **Keeps trying if an alert cannot be sent.** If neither the email nor the Pushover message goes out, the plugin tries again every minute for as long as the sensor is wet, so a real leak is never lost because your mail was down.
- **Can repeat the alert** every so many minutes while the sensor stays wet, if you ask it to.
- **Sends a test alert** from the Plugins menu, so you can check your phone and inbox get it without pouring water on the sensor.
- **Gets ready for the next leak** once the sensor reads dry again.

## Where to go next

| If you want to... | Read |
|---|---|
| Install the plugin and point it at your sensor | [Getting started](getting-started.md) |
| See what the alerts look like | [The alerts](alerts.md) |
| Understand what the plugin is doing behind the scenes | [How it works](how-it-works.md) |
| Know what every setting does | [Settings](settings.md) |
| Know what each item in the Plugins menu does | [The plugin menu](plugin-menu.md) |
| Sort out a problem | [When something goes wrong](troubleshooting.md) |
| See what changed in each version | [Version history](changelog.md) |

## Download

The latest version is always on the [Releases page](https://github.com/Highsteads/WaterLeakMonitor/releases/latest).
