# Water Leak Monitor

An [Indigo](https://www.indigodomo.com) plugin that monitors a water leak sensor and sends
Pushover and email alerts with confirmation retests to avoid false alarms.

## Features

- Polls a Zigbee water leak sensor every 2 seconds
- Confirmation retest before alerting (1 × 5s) to eliminate false triggers
- Pushover push notification on confirmed leak
- Email alert via Indigo's built-in Email+ plugin
- Auto-clears alert flag when sensor returns to dry
- Handles sensor offline/unavailable states gracefully

## Requirements

- Indigo 2021.2 or later (macOS, arm64/x86_64)
- A water leak sensor device visible in Indigo (Zigbee, Z-Wave, etc.)
- [Pushover plugin for Indigo](https://www.indigodomo.com/pluginstore/) (io.thechad.indigoplugin.pushover)
- Email+ plugin (bundled with Indigo 2021.2+)

## Installation

1. Go to the [Releases](https://github.com/Highsteads/WaterLeakMonitor/releases) page and download `WaterLeakMonitor.indigoPlugin.zip`
2. Unzip the downloaded file — you will get `WaterLeakMonitor.indigoPlugin`
3. Double-click `WaterLeakMonitor.indigoPlugin` — Indigo will install it automatically

## Configuration

Edit the constants at the top of `Contents/Server Plugin/plugin.py`:

```python
LEAK_SENSOR_ID  = 5913615   # Indigo device ID of your water leak sensor
EMAIL_TO        = "your-alert@example.com"
EMAIL_SUBJECT   = "[URGENT ALERT] Water Leak Detected"
```

## Credentials

This plugin uses **Pushover** for push notifications. The Pushover user token is loaded
from the master secrets file:

`/Library/Application Support/Perceptive Automation/IndigoSecrets.py`

Copy the relevant line from `Contents/Server Plugin/IndigoSecrets_example.py` into that file:

```python
PUSHOVER_USER_TOKEN = "your-pushover-user-token-here"
```

If `IndigoSecrets.py` is not present, the token falls back to an empty string and Pushover
alerts will be skipped (email will still be sent).

## Author

CliveS & Claude Sonnet 4.6
