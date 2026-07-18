# Water Leak Monitor

An [Indigo](https://www.indigodomo.com) plugin that monitors a water leak sensor and sends
Pushover and email alerts with confirmation retests to avoid false alarms.

## Features

- Polls a water leak sensor every 2 seconds
- Works with Zigbee2MQTT (`waterLeak` state) and Z-Wave sensors (falls back to `onOffState`)
- Confirmation retest before alerting (1 × 5s) to eliminate false triggers
- Pushover push notification on confirmed leak
- Email alert via Indigo's built-in Email+ plugin
- **Never silently drops a confirmed leak** — if an alert can't be delivered (email or Pushover down) it keeps retrying until it gets through, rather than assuming it was sent
- Optional re-alert while a leak keeps flowing, so a persisting flood keeps nagging
- **Send Test Alert** menu item to verify Pushover and email delivery without a real leak
- Auto-clears the alert once the sensor returns to dry
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

Open **Plugins → Water Leak Monitor → Configure** and fill in:

| Field | Meaning |
|---|---|
| Leak Sensor Device ID | Indigo device ID of the water leak sensor to monitor |
| Alert Email Address | Recipient for leak-alert emails (fallback if `WATERLEAK_ALERT_EMAIL` is not in `IndigoSecrets.py`) |
| Email Subject | Subject line for the alert email |
| Re-alert every (minutes) | If a confirmed leak keeps flowing, re-send the alert this often. `0` = alert once only (default) |

After saving, use **Plugins → Water Leak Monitor → Send Test Alert** to confirm your Pushover and email delivery actually work.

## Credentials — `IndigoSecrets.py` vs `IndigoSecrets_example.py`

This plugin (along with all CliveS Indigo plugins) reads sensitive values from
a shared master credentials file at:

`/Library/Application Support/Perceptive Automation/IndigoSecrets.py`

| File | Purpose | Real data? | Committed to GitHub? |
|------|---------|------------|----------------------|
| `IndigoSecrets.py` | Working file the plugin reads at runtime. Keep a backup in a password manager. | YES | **NO** — listed in `.gitignore` |
| `IndigoSecrets_example.py` | Template only — empty placeholders. Shipped in the plugin bundle. | NO | YES |

If you do not have `IndigoSecrets.py`, copy `IndigoSecrets_example.py` from
the plugin bundle to `/Library/Application Support/Perceptive Automation/` and rename it to `IndigoSecrets.py`, then fill in your values. Or skip
`IndigoSecrets.py` entirely and enter values via the plugin's configuration
dialog — `IndigoSecrets.py` wins over the dialog when both are set.

If a required value is set in NEITHER source the plugin logs an ERROR
pointing the user to either fill in the matching field or add the key to
`IndigoSecrets.py`.

## Logging

Every log line is prefixed with a millisecond timestamp `[HH:MM:SS.mmm]` so
events can be correlated tightly with other CliveS plugins (Device Activity
Monitor uses the same convention).

To turn the prefix off (or back on) at any time:

**Plugins → Water Leak Monitor → Toggle Timestamps in Log (on/off)**

## Version history

- **1.9** (18-07-2026) — deep-review improvements: a Send Test Alert menu item to verify delivery without a real leak, an optional re-alert while a leak keeps flowing, and Show Plugin Info now reports the monitored sensor and its state.
- **1.8** (18-07-2026) — deep-review safety fixes: a confirmed leak whose alert could not be delivered is no longer silently treated as sent — it keeps retrying until it gets through. The monitor loop can no longer be stopped by an unexpected error, Z-Wave sensors (which expose `onOffState`) are now monitored, and the alert names your actual sensor. First test suite added.
- **1.6** (23-05-2026) — millisecond timestamp prefix on every log line and a Toggle Timestamps menu item.

The setting is stored in `pluginPrefs` (`timestampEnabled`) and persists across
restarts. Defaults to ON.

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
