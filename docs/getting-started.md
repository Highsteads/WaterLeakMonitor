---
title: Getting started
nav_order: 2
---

# Getting started

This takes about five minutes, and you only do it once.

## What you need

- Indigo 2022.1 or later.
- A water leak sensor that already works in Indigo — a Zigbee sensor, a Z-Wave sensor, or any other kind that shows as on when it is wet.
- At least one way for the plugin to reach you, and ideally both:
  - the **Pushover** plugin for Indigo, from the Indigo Plugin Store, installed, enabled and set up to send to your phone, and
  - Indigo's own **Email+** plugin, which comes with Indigo, with an outgoing mail account set up in it.

## 1. Install the plugin

1. Go to the [Releases page](https://github.com/Highsteads/WaterLeakMonitor/releases/latest) and download `WaterLeakMonitor.indigoPlugin.zip`
2. Unzip the downloaded file — you will get `WaterLeakMonitor.indigoPlugin`
3. Double-click `WaterLeakMonitor.indigoPlugin` — Indigo will install it automatically

Indigo asks whether to enable the plugin. Say yes.

## 2. Find your sensor's ID number

The plugin knows your sensor by the ID number Indigo gives every device. To find it, right-click the sensor in Indigo's main window and choose **Copy ID**. The number is now on the clipboard, ready to paste.

## 3. Fill in the settings

Open **Plugins → Water Leak Monitor → Configure**.

1. Paste the number into **Leak Sensor Device ID**. The box starts with the number of my own sensor, which will not exist on your system, so replace it.
2. Type the address the email alerts should go to into **Alert Email Address**.
3. Leave the rest as they are to start with, and click **Save**.

Every setting is explained on the [Settings](settings.md) page, which also shows how to keep the email address in a shared file instead.

## 4. Check it works

When you click **Save**, the Event Log says **Plugin configuration updated**, and the new settings are in use straight away.

Now choose **Plugins → Water Leak Monitor → Send Test Alert (verify Pushover + email)**. Your phone should show a Pushover message and your inbox an email, both with **(TEST)** after the sensor's name. The Event Log says whether each one was handed over.

Each time the plugin starts, the Event Log names the sensor's ID number and the email address it is using, so you can check them there too.

If the test does not arrive, the [When something goes wrong](troubleshooting.md) page goes through the usual causes.
