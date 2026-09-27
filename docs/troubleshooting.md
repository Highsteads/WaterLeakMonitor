---
title: When something goes wrong
nav_order: 7
---

# When something goes wrong

Each section starts with what you see, then what it means and what to do.

## The log says "Leak sensor not found" every two seconds

The number in **Leak Sensor Device ID** does not match any device in Indigo, so nothing is being watched.

- Right-click your leak sensor in Indigo's main window, choose **Copy ID**, and paste the number into **Plugins → Water Leak Monitor → Configure → Leak Sensor Device ID**.
- If you deleted the sensor and added it again, it has a new ID number, so copy the new one.

The lines stop as soon as you click **Save** with the right number.

## The log says "No alert email configured"

Neither the **Alert Email Address** setting nor the shared `IndigoSecrets.py` file has an address, so no email alerts can go out. Pushover alerts still can. Fill in the address as the [Settings](settings.md) page describes.

## The log says "Pushover plugin not available — skipping push alert"

The Pushover plugin is not installed, or is disabled. Install it from the Indigo Plugin Store, or enable it in **Plugins → Manage Plugins**, and set it up to send to your phone. Email alerts still go out without it.

## The log says a leak is confirmed but no alert could be delivered

Neither the email nor the Pushover message could be sent. The plugin tries again every 60 seconds for as long as the sensor stays wet, so deal with the leak first, then:

- Check the Pushover plugin is enabled.
- Check Email+ has a working outgoing mail account.
- Look at the lines just above in the Event Log, which say what went wrong with each.

## The test alert says it was delivered, but nothing arrived

The plugin handed the alerts over without an error, so the trouble lies further along.

- For the email, check the Email+ plugin's mail account, and your junk mail folder.
- For the Pushover message, check the Pushover plugin is set up with your details, and that the Pushover app on your phone is signed in.

## The test alert failed on both

Neither Email+ nor the Pushover plugin would take the alert. The Event Log lines just above say why for each one. The two sections above cover the usual causes.

## My sensor stopped answering and I was not told

The plugin does not report a sensor that has gone quiet or into error — it only watches for water. While the sensor is in error it sends no alerts. Keep an eye on the sensor in Indigo's device list, and check its battery if it runs on one.

## I keep getting the same alert every few minutes

**Re-alert every (minutes)** is set above nought, and the sensor is still wet. Once the sensor is dry the repeats stop. To have one alert per leak, set it to 0.

## Still stuck?

Choose **Plugins → Water Leak Monitor → Show Plugin Info**, copy the lines it writes to the Event Log, and post them on the [Indigo forum](https://forums.indigodomo.com) with a description of what you see. You can also [raise an issue on GitHub](https://github.com/Highsteads/WaterLeakMonitor/issues).
