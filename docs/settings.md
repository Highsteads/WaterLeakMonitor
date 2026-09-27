---
title: Settings
nav_order: 5
---

# Settings

All the settings are in one place. Open them with **Plugins → Water Leak Monitor → Configure**. A change takes effect as soon as you click **Save**.

| Setting | What it does |
|---|---|
| **Leak Sensor Device ID** | The ID number Indigo gives your leak sensor. Right-click the sensor in Indigo's main window and choose **Copy ID** to get it. The box starts empty, and while it is empty the plugin watches nothing and says so once in the Event Log. If it holds something that is not a number, the Event Log says that once too. |
| **Alert Email Address** | The address the email alerts go to. If the shared `IndigoSecrets.py` file described below holds an address, that one is used instead and this box is ignored. |
| **Email Subject** | The subject line of the email alerts. It starts as `[URGENT ALERT] Water Leak Detected`, and a blank box goes back to that. |
| **Re-alert every (minutes)** | While the sensor stays wet, the plugin sends the alerts again this often. Nought, the starting value, means one alert per leak. A blank box or anything that is not a whole number counts as nought. |
| **Enable Debug Logging** | Adds extra lines to the Event Log for chasing a problem, such as a note when the sensor drops out for a moment too short to message you about. Leave it unticked day to day. |

The two-second check and the five-second wait before an alert are fixed, and are not settings.

## Keeping the email address in one file

If you run several of my plugins, you can keep the alert address in one shared file instead of typing it into the plugin. The file is called `IndigoSecrets.py` and lives in `/Library/Application Support/Perceptive Automation/`.

A blank copy, `IndigoSecrets_example.py`, comes inside the plugin. To use it:

1. Copy `IndigoSecrets_example.py` to `/Library/Application Support/Perceptive Automation/`.
2. Rename the copy `IndigoSecrets.py`.
3. Fill in the line `WATERLEAK_ALERT_EMAIL = ""` with your address between the quotes.
4. Restart the plugin, as it reads the file when it starts.

When the file has an address, it is used, whatever the Configure box says. This plugin needs nothing else from the file.

If neither the file nor the Configure box has an address, the Event Log shows a red line saying no alert email is configured, each time the plugin starts. Pushover alerts still go out.
