# Runbook: Discord bot not responding

When Astra's Discord bot stops responding to messages or commands, use this runbook to diagnose and fix.

## 1. Verify bot token and permissions

- **Discord token**: The bot uses a token from config or environment (e.g. `DISCORD_BOT_TOKEN` or from a config file). Ensure the token is valid and not revoked in the Discord Developer Portal.
- **Bot permissions**: In the Discord server, the bot needs at least: Read Message History, Send Messages, Read Messages/View Channels (and any required for your slash commands or intents). Check Server Settings, Integrations, then your bot Permissions.
- **Intents**: If the bot uses privileged intents (e.g. message content, members), ensure they are enabled in the Developer Portal (Bot, Privileged Gateway Intents) and that the app requests them when creating the client.

## 2. Check ASTRA_CONFIG_DIR and config

- **ASTRA_CONFIG_DIR**: Must point to the directory containing your config JSON files. If unset or wrong, the app may fail to load Discord config or start the bot. Example: `export ASTRA_CONFIG_DIR=/path/to/config`
- **Discord-related config**: Look for a config file that holds the bot token and any Discord-specific settings. Confirm the token and channel IDs (if used) are correct.

## 3. Check logs for exceptions

- **InfluenceError**: Can indicate S3 or mind load/save failures; if the bot blocks on mind load at startup, it may never connect to Discord. See mind-file-not-loading.md.
- **ConfigurationError**: Raised when required config is missing. Fix config paths and keys so the Discord client can be created.
- **Discord API errors**: Look for discord.errors, 401 Unauthorized (bad token), 403 Forbidden (permissions), or rate-limit messages. Adjust token, permissions, or back off on request rate.

## 4. Verify network and firewall

- The process must be able to reach Discord's gateway and API (e.g. discord.com, gateway.discord.gg). Check firewall, proxy, and outbound rules.
- If running in a restricted environment, ensure WebSocket and HTTPS to Discord are allowed.

## 5. Process and connectivity state (optional)

- Confirm the Astra process is running and the main event loop is not stuck (e.g. no long blocking call before or inside the Discord client start).
- If you have a heartbeat or readiness check, use it to see if the process is alive and whether the Discord client reports as connected.

## 6. Quick checklist

- [ ] Bot token valid and not revoked in Developer Portal?
- [ ] Bot has required permissions in the server?
- [ ] Privileged intents enabled in Developer Portal if used?
- [ ] ASTRA_CONFIG_DIR set and Discord config present and correct?
- [ ] Logs show ConfigurationError, InfluenceError, or Discord API errors?
- [ ] Network/firewall allows outbound access to Discord?

If all of the above are correct and the bot still does not respond, capture the full traceback and log snippet (redact the bot token) for further debugging.
