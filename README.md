# Water Leak Monitor for Indigo

**Watch a water leak sensor from Indigo, and get a Pushover message and an email the moment it finds water.**

**Version:** 1.11.0 | **Author:** CliveS & Claude | **Needs:** Indigo 2022.1 or later, a leak sensor in Indigo, and the Pushover plugin or Email+ set up

**[Read the full guide](https://highsteads.github.io/WaterLeakMonitor/)** — setting up, what the alerts look like, and what to do when something goes wrong.

---

## What it does

This plugin lets [Indigo](https://www.indigodomo.com) keep watch on a water leak sensor you already have. I use it on the sensor by the boiler in the bathroom, where a slow drip could go unseen for days.

- **Checks your leak sensor every two seconds.**
- **Checks a second time before it alerts,** five seconds later, so a sensor that reads wet for a moment does not wake you for nothing.
- **Sends a Pushover message and an email** naming the sensor and the time. The Pushover message goes at emergency priority with a siren sound, and Pushover repeats it every 10 minutes until you acknowledge it. Both can be changed in the settings.
- **Keeps trying if an alert cannot be sent.** If neither the email nor the Pushover message goes out, the plugin tries again every minute while the sensor is wet, so a real leak is never lost because your mail was down.
- **Repeats the alert** every 15 minutes while the sensor stays wet. You can change how often, or turn it off.
- **Tells you when the sensor stops answering,** and again when it is back. That covers a sensor Indigo shows in error, one that is disabled or deleted, and one that has reported nothing for 12 hours, which is what a flat battery usually looks like. If the sensor was wet when it stopped answering, the message is urgent.
- **Warns you when the battery is low,** at 20% by default, if your sensor reports its battery to Indigo.
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

**v1.11.0** — Harder to miss a leak. A sensor that goes quiet for 12 hours, or is deleted, now counts as not answering and you are told. A low battery is reported. A sensor that drops out while wet sends an urgent message. Leak alerts now go at Pushover emergency priority with a siren and repeat every 15 minutes. A setting you had already saved, such as a re-alert of 0, is kept.

**v1.10.0** — The plugin now tells you when your leak sensor stops answering, and again when it is back. The sensor box in the settings starts empty instead of holding my own sensor's number.

**v1.9.3** — The plugin carries a note of where its code lives on GitHub, the same way other Indigo plugins do. Nothing else changed.

**v1.9.2** — The help text in the settings window is no longer cut off part way through. No setting or behaviour changed.

Every version is listed in the [version history](https://highsteads.github.io/WaterLeakMonitor/changelog.html).

## Authors & licence

Vibed into existence by **CliveS**, who knew what he wanted, argued until he got it, and tested it on a real house. Typed at inhuman speed by **Claude** (Anthropic), who mostly did as it was told.

© 2026 CliveS · [MIT licence](LICENSE) — copy it, fork it, bend it, break it, fix it, ship it. If it breaks, you get to keep both pieces.
