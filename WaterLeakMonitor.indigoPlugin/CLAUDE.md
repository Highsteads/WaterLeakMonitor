# Water Leak Monitor Plugin - Claude Context

## Plugin Overview
Indigo plugin for monitoring water leak sensors and freezer lid status with Pushover alert integration. Provides real-time notifications for leak detection and temperature alerts.

## Important Rules
- Do NOT guess at API methods or command names. Read existing plugin code first to understand actual available APIs.
- Always check existing plugin code before suggesting API methods - do NOT guess Indigo API calls
- Always run/test scripts after editing when possible, don't assume changes work.
- Never fabricate issues that don't exist in the code - verify before reporting bugs

## Plugin-Specific Context

### Technology Stack
- **Integration**: Pushover notifications
- **Devices**: Water leak sensors, freezer lid sensors
- **Notifications**: Push alerts via Pushover plugin

### Key Concepts
- Monitor sensor states for leak/open conditions
- Send Pushover alerts when leaks detected or freezer lid left open
- Filter false alarms during system reboots
- Handle sensor offline/unavailable states gracefully

### Pushover Integration
```python
# Correct method to send Pushover notifications
pushover_plugin = indigo.server.getPlugin('io.thechad.indigoplugin.pushover')
# Bundle ID: com.clives.indigoplugin.waterleakmonitor (changed from com.highsteads in v1.5)
if pushover_plugin.isEnabled():
    # Use proper Pushover API - DO NOT GUESS method names!
    # Check existing code for correct API calls
```

### Common Issues to Watch For
1. **False Alarms**: Filter out alerts during HA/system reboots
2. **Pushover API**: Always verify correct method names from existing code - don't guess!
3. **Sensor Offline**: Handle unavailable sensors without crashing
4. **Alert Throttling**: Prevent spam alerts for same condition
5. **UTF-8 Encoding**: Handle £ symbol in messages properly

### Indigo Plugin Lifecycle
- `startup()` - Initialize monitoring timers
- `shutdown()` - Clean up timers and threads
- `deviceStartComm(device)` - Start monitoring specific sensors
- `deviceStopComm(device)` - Stop monitoring

### Alert Logic
- Check sensor state changes
- Evaluate alert conditions (leak detected, lid open duration)
- Send Pushover notification with appropriate priority
- Track alert history to prevent duplicates

## Coding Standards
- Use UTF-8 encoding for all Python files (handle £ symbol properly)
- Follow existing code style and naming conventions in plugin.py
- Validate sensor states before triggering alerts
- Log all alert decisions for debugging

## Testing Checklist
- [ ] Plugin starts without errors
- [ ] Leak sensors detected and monitored
- [ ] Pushover alerts send successfully
- [ ] False alarm filtering works during reboots
- [ ] Plugin shuts down cleanly
- [ ] Offline sensors handled gracefully

## Last Updated
2026-02-11
