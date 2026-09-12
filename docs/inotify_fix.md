# Fixing "inotify resources exhausted" Error

## Problem

When running `tail -f ~/astra_logs/*.log`, you may see:
```
tail: inotify resources exhausted
tail: inotify cannot be used, reverting to polling
```

This happens when the system runs out of inotify watch descriptors.

## Solutions

### Option 1: Use journalctl (Recommended)

Since Astra runs as a systemd service, use `journalctl` instead:

```bash
# Watch live logs
journalctl --user -u astra -f

# Or use the watch script
./watch_astra.sh
```

This is more efficient and doesn't consume inotify watches.

### Option 2: Use the watch_logs.sh script

A script is available that handles log watching more efficiently:

```bash
./scripts/watch_logs.sh
```

### Option 3: Increase inotify limit (if needed)

If you must use `tail -f` on many files, increase the system limit:

```bash
# Check current limit
cat /proc/sys/fs/inotify/max_user_watches

# Increase temporarily (until reboot)
sudo sysctl fs.inotify.max_user_watches=524288

# Make permanent
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Note:** The default is usually 65536. Increasing to 524288 should handle most cases.

## Why journalctl is better

- More efficient (doesn't use inotify for each file)
- Handles log rotation automatically
- Includes systemd metadata (timestamps, service info)
- Works even if log files are rotated/deleted
- Single command watches all logs
