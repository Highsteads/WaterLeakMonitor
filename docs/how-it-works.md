---
title: How it works
nav_order: 4
---

# How it works

You do not need to know any of this to use the plugin. It is here for anyone who likes to know what is going on.

## Checking every two seconds

Every two seconds the plugin looks at your leak sensor in Indigo and reads whether it is wet.

- If the sensor has its own **water leak** reading, as Zigbee sensors added through Zigbee2MQTT do, the plugin reads that.
- If not, it reads whether the sensor shows **on**, which is how Z-Wave and most other leak sensors show water.

It watches one sensor, the one whose ID number is in the settings.

## Checking twice before it alerts

When the sensor first reads wet, the Event Log says **LEAK DETECTED — starting confirmation process**. The plugin then waits five seconds and looks again.

- **Still wet** — the log says **LEAK CONFIRMED after retests**, and the plugin sends the alerts.
- **Dry again** — the log says the leak cleared and calls it a false alarm. No alert goes out.

If the sensor reads wet again later, the whole check starts again, so a leak that comes and goes is still caught.

## Making sure the alert gets out

The plugin sends the email and the Pushover message together. It counts the alert as sent when at least one of them is accepted — by Email+ for the email, or by the Pushover plugin for the message — without an error.

If neither is accepted, the Event Log shows a red line saying the leak is confirmed but no alert could be delivered, and the plugin tries again every 60 seconds for as long as the sensor stays wet. It never marks a leak as dealt with until an alert has gone out.

Once one alert has gone out, the plugin does not send another for the same leak unless you have asked for repeats with **Re-alert every (minutes)**.

## When the sensor reads dry

When the sensor reads dry again, the Event Log says **Leak sensor cleared** and the plugin is ready for the next leak. It sends no all-clear message.

## When the sensor itself has a problem

If Indigo shows the sensor with an error, which is how many plugins show a device that has stopped answering, the plugin leaves it alone and sends no alert until the error clears. If the error comes in the middle of a leak, the plugin starts afresh when the sensor comes back, so a sensor that is still wet then brings a new alert.

The plugin does not tell you when your sensor stops answering. If that matters to you, keep an eye on the sensor in Indigo's device list, where a device in error shows in red.

## What goes in the log

The plugin's lines in the Event Log start with the time to the thousandth of a second, such as `[09:15:04.271]`, which helps when lining events up. The [plugin menu](plugin-menu.md) has an item to turn that off.
