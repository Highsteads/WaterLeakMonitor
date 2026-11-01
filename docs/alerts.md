---
title: The alerts
nav_order: 3
---

# The alerts

When your sensor finds water and is still wet five seconds later, the plugin sends two alerts at once — a Pushover message and an email. Both name the sensor, using the name you gave it in Indigo, and the date and time.

## The Pushover message

| Part | What it says |
|---|---|
| **Title** | [URGENT] Water Leak |
| **Message** | LEAK DETECTED at *your sensor's name*, with the time on the next line, such as `Time: 2026-09-27 09:15:04` |
| **How it arrives** | At high priority, which Pushover shows even during the quiet hours you set in its app, and with the phone set to vibrate rather than play a sound |

The message goes to whoever the Pushover plugin is set up to send to.

## The email

| Part | What it says |
|---|---|
| **To** | The address in **Alert Email Address**, or in the shared `IndigoSecrets.py` file if you keep it there |
| **Subject** | The **Email Subject** setting, which starts as `[URGENT ALERT] Water Leak Detected` |
| **Body** | Three lines: LEAK DETECTED at *your sensor's name*, the time, and **Status: ACTIVE** |

The email goes out through Indigo's own Email+ plugin, using the mail account set up there.

## Repeat alerts

If you set **Re-alert every (minutes)** to a number above nought, the plugin sends both alerts again each time that many minutes pass while the sensor stays wet. The repeats look exactly like the first alert, with the time they were sent. It starts as nought, which means one alert per leak.

## Test alerts

**Send Test Alert** in the Plugins menu sends the same two alerts, with **(TEST)** after the sensor's name. The title, the subject and the priority are the same as a real alert's, so the test shows you exactly what a real one will look like on your phone.

## When the sensor stops answering

If Indigo shows your sensor with an error, or you disable it, the plugin cannot see whether it is wet, so it tells you. This is not a leak alert, so the Pushover message goes at normal priority.

| Part | What it says |
|---|---|
| **Pushover title** | Leak sensor not answering |
| **Email subject** | Water Leak Monitor: Leak sensor not answering |
| **Message** | *Your sensor's name* has stopped answering, with what Indigo shows for it, such as "no ack", and a promise of another message when it is back |

When the sensor answers again, a second message titled **Leak sensor back** says how long it was gone, such as "after 12 minutes". You get no more than one "not answering" message every half an hour, however often the sensor drops in and out.

## When the water clears

The plugin sends no all-clear message. When the sensor reads dry again, the Event Log says **Leak sensor cleared**, and the next time the sensor reads wet the plugin alerts you afresh.
