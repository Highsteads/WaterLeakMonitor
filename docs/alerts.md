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
| **How it arrives** | At the **Pushover leak priority** you choose. It starts at Emergency, which Pushover repeats every 10 minutes, for up to 24 hours, until you tap Acknowledge in its app. High sends it once. Both get through the quiet hours you set in the Pushover app. The sound is **Pushover leak sound**, siren to start with. |

The message goes to whoever the Pushover plugin is set up to send to.

## The email

| Part | What it says |
|---|---|
| **To** | The address in **Alert Email Address**, or in the shared `IndigoSecrets.py` file if you keep it there |
| **Subject** | The **Email Subject** setting, which starts as `[URGENT ALERT] Water Leak Detected` |
| **Body** | Three lines: LEAK DETECTED at *your sensor's name*, the time, and **Status: ACTIVE** |

The email goes out through Indigo's own Email+ plugin, using the mail account set up there.

## Repeat alerts

While the sensor stays wet, the plugin sends both alerts again every **Re-alert every (minutes)**. The repeats look exactly like the first alert, with the time they were sent. It starts at 15 minutes. Set it to 0 for one alert per leak. If you saved the settings before version 1.11.0, your saved value, often 0, is kept.

## Test alerts

**Send Test Alert** in the Plugins menu sends the same two alerts, with **(TEST)** after the sensor's name. The title, the subject and the priority are the same as a real alert's, so the test shows you exactly what a real one will look like on your phone.

## When the sensor stops answering

If Indigo shows your sensor with an error, you disable it, it is deleted from Indigo, or it reports nothing for longer than **Quiet sensor alarm after (hours)**, the plugin cannot see whether it is wet, so it tells you. This is not a leak alert, so the Pushover message goes at normal priority. If neither the email nor the Pushover message can be sent, it tries again every 5 minutes.

| Part | What it says |
|---|---|
| **Pushover title** | Leak sensor not answering |
| **Email subject** | Water Leak Monitor: Leak sensor not answering |
| **Message** | *Your sensor's name* has stopped answering, with the reason, such as "no ack", "no change reported for about 13 hours" or that Indigo has no device with its ID, and a promise of another message when it is back |

When the sensor answers again, a second message titled **Leak sensor back** says how long it was gone, such as "after 12 minutes". You get no more than one "not answering" message every half an hour, however often the sensor drops in and out.

## When the sensor stops answering while wet

If the last reading was wet when the sensor stopped answering, you also get an urgent message, at the leak alert's priority and sound.

| Part | What it says |
|---|---|
| **Pushover title** | [URGENT] Leak sensor lost while WET |
| **Email subject** | Water Leak Monitor: [URGENT] Leak sensor lost while WET |
| **Message** | The last reading from *your sensor's name* was WET, it has stopped answering, and you should go and look |

It is retried every minute until one of the two goes out.

## When the battery is low

If the sensor reports its battery to Indigo, you get a normal-priority message titled **Leak sensor battery low**, with the percentage, when it is at or below **Low battery warning at (%)**. It repeats once a day until the battery reads at least 10% above that level again.

## When the water clears

The plugin sends no all-clear message. When the sensor reads dry again, the Event Log says **Leak sensor cleared**, and the next time the sensor reads wet the plugin alerts you afresh.
