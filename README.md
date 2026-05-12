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

- Indigo 2022.1 or later (Python 3.10+ bundled with Indigo)
- macOS (arm64 or x86_64)
- A water leak sensor device visible in Indigo (Zigbee, Z-Wave, etc.)
- [Pushover plugin for Indigo](https://www.indigodomo.com/pluginstore/) (io.thechad.indigoplugin.pushover)
- Email+ plugin (bundled with Indigo)

*Developed and tested on Indigo 2025.2 / Python 3.13. Older Indigo releases that meet the minimum API version above should also work — the API floor is what Indigo's plugin loader actually checks.*

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

## Credentials — `IndigoSecrets.py` vs `IndigoSecrets_example.py`

This plugin (along with all CliveS Indigo plugins) reads sensitive values from
a shared master credentials file at:

`/Library/Application Support/Perceptive Automation/IndigoSecrets.py`

| File | Purpose | Real data? | Committed to GitHub? |
|------|---------|------------|----------------------|
| `IndigoSecrets.py` | Working file the plugin reads at runtime. Keep a backup in a password manager. | YES | **NO** — listed in `.gitignore` |
| `IndigoSecrets_example.py` | Template only — empty placeholders. Shipped in the plugin bundle. | NO | YES |

If you do not have `IndigoSecrets.py`, copy `IndigoSecrets_example.py` from
the plugin bundle to that location and fill in your values. Or skip
`IndigoSecrets.py` entirely and enter values via the plugin's configuration
dialog — `IndigoSecrets.py` wins over the dialog when both are set.

If a required value is set in NEITHER source the plugin logs an ERROR
pointing the user to either fill in the matching field or add the key to
`IndigoSecrets.py`.
## Author

CliveS & Claude Sonnet 4.6
