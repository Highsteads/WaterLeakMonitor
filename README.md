# Water Leak Monitor

**Version:** 1.9.3

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

This plugin, like every CliveS Indigo plugin, reads sensitive values from one
shared master file:

`/Library/Application Support/Perceptive Automation/IndigoSecrets.py`

| File | Purpose | Real data? | Committed to GitHub? |
|------|---------|------------|----------------------|
| `IndigoSecrets.py` | Working file the plugin reads at runtime. Keep a backup in a password manager. | YES | **NO** — listed in `.gitignore` |
| `IndigoSecrets_example.py` | Template only — empty placeholders. Shipped in the plugin bundle. | NO | YES |

If you don't have `IndigoSecrets.py`, copy `IndigoSecrets_example.py` out of
the plugin bundle into `/Library/Application Support/Perceptive Automation/`,
rename it to `IndigoSecrets.py`, and fill in your values. Or skip the file
altogether and type the values into the plugin's configuration dialog — where
both are set, `IndigoSecrets.py` wins.

If neither source supplies a value the plugin needs, it logs an ERROR naming
the key and telling you to either fill in the matching field or add the key to
`IndigoSecrets.py`.

## Logging

Every log line carries a millisecond timestamp `[HH:MM:SS.mmm]`, so you can
line events up precisely against the other CliveS plugins — Device Activity
Monitor uses the same format.

To turn the prefix off, or back on, at any time:

**Plugins → Water Leak Monitor → Toggle Timestamps in Log (on/off)**

The plugin stores the setting in `pluginPrefs` (`timestampEnabled`) and it
survives a restart. It defaults to ON.

## Version history


**v1.9.3** - **The bundle now carries the standard GitHub record.** Indigo plugins can carry a small note inside the bundle saying where their source lives on GitHub, spelt the way the Indigo Domotics and community plugins spell it. This one now has it, pointing at this repository. Nothing else changed.

**v1.9.2** - **The settings dialog was stretched wider than its own window, so the help text beside each setting was cut off mid-sentence.** The short help that can be attached to a setting is drawn on a single line and never wraps, so the longest one decides how wide every row is — and the window cannot be widened past a fixed maximum. The one long one have moved into ordinary description paragraphs, which do wrap. Two new checks fail the build if any help text or setting label grows long enough to do it again. No setting or behaviour changed.
- **1.9.1** (21-07-2026) — housekeeping. Shared-utility refresh: calling the log timestamp filter twice no longer double-stamps every line, and the module imports cleanly outside Indigo.
- **1.9** (18-07-2026) — deep-review improvements: a Send Test Alert menu item to verify delivery without a real leak, an optional re-alert while a leak keeps flowing, and Show Plugin Info now reports the monitored sensor and its state.
- **1.8** (18-07-2026) — deep-review safety fixes: a confirmed leak whose alert could not be delivered is no longer silently treated as sent — it keeps retrying until it gets through. The monitor loop can no longer be stopped by an unexpected error, Z-Wave sensors (which expose `onOffState`) are now monitored, and the alert names your actual sensor. First test suite added.
- **1.7** (05-06-2026) — estate bug-sweep. The leak sensor's device ID is now read defensively. The old code only coped with the field being blank, so anything non-numeric left in it crashed the plugin on load and again on saving the settings dialog.
- **1.6** (23-05-2026) — millisecond timestamp prefix on every log line and a Toggle Timestamps menu item.
- **1.5** (13-05-2026) — the alert email address moved into `IndigoSecrets.py` (`WATERLEAK_ALERT_EMAIL`) with a settings-dialog fallback, and the leak sensor's device ID moved out of the source into the settings, so the plugin works for anyone rather than only for one sensor ID. A new `PluginConfig.xml` means the whole thing can be set up without editing any code.

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
