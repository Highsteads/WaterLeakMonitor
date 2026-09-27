# Water Leak Monitor for Indigo

**Watch a water leak sensor from Indigo, and get a Pushover message and an email the moment it finds water.**

**Version:** 1.9.3 | **Author:** CliveS & Claude | **Needs:** Indigo 2022.1 or later, a leak sensor in Indigo, and the Pushover plugin or Email+ set up

**[Read the full guide](https://highsteads.github.io/WaterLeakMonitor/)** — setting up, what the alerts look like, and what to do when something goes wrong.

---

## What it does

This plugin lets [Indigo](https://www.indigodomo.com) keep watch on a water leak sensor you already have. I use it on the sensor by the boiler in the bathroom, where a slow drip could go unseen for days.

- **Checks your leak sensor every two seconds.**
- **Checks a second time before it alerts,** five seconds later, so a sensor that reads wet for a moment does not wake you for nothing.
- **Sends a Pushover message and an email** naming the sensor and the time. The Pushover message goes at high priority and makes the phone vibrate.
- **Keeps trying if an alert cannot be sent.** If neither the email nor the Pushover message goes out, the plugin tries again every minute while the sensor is wet, so a real leak is never lost because your mail was down.
- **Can repeat the alert** every so many minutes while the sensor stays wet.
- **Sends a test alert** from the Plugins menu, so you can check both reach you without a real leak.

## What it works with

- **Leak sensors:** Zigbee sensors added through Zigbee2MQTT, Z-Wave sensors, and any other leak sensor that Indigo shows as on when it is wet. The plugin watches one sensor.
- **Pushover:** the Pushover plugin for Indigo, from the Indigo Plugin Store.
- **Email:** Indigo's own Email+ plugin, with an outgoing mail account set up in it.

You need at least one of Pushover and Email+, and I recommend both.

## Installing

1. Go to the [Releases page](https://github.com/Highsteads/WaterLeakMonitor/releases/latest) and download `WaterLeakMonitor.indigoPlugin.zip`
2. Unzip the downloaded file — you will get `WaterLeakMonitor.indigoPlugin`
3. Double-click `WaterLeakMonitor.indigoPlugin` — Indigo will install it automatically

## Setting it up

1. In Indigo's main window, right-click your leak sensor and choose **Copy ID**.
2. Open **Plugins → Water Leak Monitor → Configure**, paste the number into **Leak Sensor Device ID**, fill in **Alert Email Address**, and click **Save**.
3. Choose **Plugins → Water Leak Monitor → Send Test Alert (verify Pushover + email)**, and check your phone and inbox.

The [full guide](https://highsteads.github.io/WaterLeakMonitor/) goes through each step, explains every setting, and covers what to do if something does not work.

## What's new

**v1.9.3** — The plugin carries a note of where its code lives on GitHub, the same way other Indigo plugins do. Nothing else changed.

**v1.9.2** — The help text in the settings window is no longer cut off part way through. No setting or behaviour changed.

**v1.9.1** — A tidy-up of the code shared with my other plugins. A log line can no longer come out with the time printed twice.

Every version is listed in the [version history](https://highsteads.github.io/WaterLeakMonitor/changelog.html).

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
