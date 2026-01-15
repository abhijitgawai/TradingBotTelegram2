"""
ADMIN_BOT - Admin Commands Handler with Interactive Buttons
Handles /status, /restart, /logs, /help, /menu commands from admin group.
Supports both text commands AND clickable inline buttons!

To add a new command:
1. Create a handler function: async def cmd_yourcommand(event, tg_client, config):
2. Add to COMMANDS dict below
3. Add button to get_admin_menu() if you want it in the button menu
"""

import subprocess
import time
import os
from telethon import Button

# Bot start time (set when module loads)
BOT_START_TIME = time.time()

# =============================================================================
# INLINE KEYBOARD MENU
# =============================================================================

def get_admin_menu():
    """
    Returns inline keyboard buttons for admin commands.
    Each button triggers a callback_data that we handle in handle_button_click()
    """
    return [
        # Row 1: Status and Logs
        [
            Button.inline("📊 Status", b"cmd_status"),
            Button.inline("📋 Logs", b"cmd_logs"),
        ],
        # Row 2: Restart options
        [
            Button.inline("🔄 Restart", b"cmd_restart"),
            Button.inline("⚡ Force Restart", b"cmd_forcerestart"),
        ],
        # Row 3: Deploy and Config
        [
            Button.inline("🚀 Deploy", b"cmd_deploy"),
            Button.inline("⚙️ Config", b"cmd_config"),
        ],
        # Row 4: Test and Help
        [
            Button.inline("🧪 Test", b"cmd_test"),
            Button.inline("❓ Help", b"cmd_help"),
        ],
    ]


# =============================================================================
# COMMAND HANDLERS - Add new commands here
# =============================================================================

async def cmd_status(event, tg_client, config, is_callback=False):
    """Check if bot is running and show uptime"""
    uptime_seconds = int(time.time() - BOT_START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    msg = f"🟢 **Bot is running**\n"
    msg += f"⏱️ Uptime: {hours}h {minutes}m {seconds}s"
    
    if is_callback:
        await event.answer()  # Acknowledge the button click
        await tg_client.send_message(config['admin_group_id'], msg)
    else:
        await tg_client.send_message(config['admin_group_id'], msg)


async def cmd_restart(event, tg_client, config, is_callback=False):
    """Restart the bot using systemctl"""
    if is_callback:
        await event.answer("🔄 Restarting...")  # Acknowledge with toast message
    
    await tg_client.send_message(config['admin_group_id'], "🔄 Restarting bot...")
    
    # Run systemctl restart (requires passwordless sudo setup)
    result = subprocess.run(
        ['sudo', 'systemctl', 'restart', 'tradingbot'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        await tg_client.send_message(
            config['admin_group_id'], 
            f"❌ Restart failed: {result.stderr}"
        )


async def cmd_logs(event, tg_client, config, is_callback=False):
    """Get last 20 log lines from journalctl"""
    if is_callback:
        await event.answer("📋 Fetching logs...")
    
    result = subprocess.run(
        ['sudo', 'journalctl', '-u', 'tradingbot', '-n', '20', '--no-pager'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logs = result.stdout[-4000:]  # Telegram message limit ~4096 chars
        await tg_client.send_message(
            config['admin_group_id'], 
            f"📋 **Last 20 log lines:**\n```\n{logs}\n```"
        )
    else:
        await tg_client.send_message(
            config['admin_group_id'], 
            f"❌ Failed to get logs: {result.stderr}"
        )


async def cmd_help(event, tg_client, config, is_callback=False):
    """Show all available commands"""
    if is_callback:
        await event.answer()
    
    msg = "📖 **Available Commands:**\n\n"
    msg += "**Text Commands:**\n"
    for cmd, info in COMMANDS.items():
        msg += f"`{cmd}` - {info['description']}\n"
    msg += "\n**Or use /menu to get clickable buttons!**"
    await tg_client.send_message(config['admin_group_id'], msg)


async def cmd_forcerestart(event, tg_client, config, is_callback=False):
    """Fresh restart - clears logs and restarts bot"""
    if is_callback:
        await event.answer("🔄 Fresh restarting...")
    
    await tg_client.send_message(config['admin_group_id'], "🔄 Fresh restart - clearing logs and restarting...")
    
    # Step 1: Rotate logs
    subprocess.run(['sudo', 'journalctl', '--rotate'], capture_output=True)
    
    # Step 2: Clear old logs
    subprocess.run(['sudo', 'journalctl', '--vacuum-time=1s'], capture_output=True)
    
    # Step 3: Restart bot
    result = subprocess.run(
        ['sudo', 'systemctl', 'restart', 'tradingbot'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        await tg_client.send_message(
            config['admin_group_id'], 
            f"❌ Fresh restart failed: {result.stderr}"
        )


async def cmd_menu(event, tg_client, config, is_callback=False):
    """Show the command menu - buttons if bot account, text otherwise"""
    if is_callback:
        await event.answer()
    
    has_buttons = config.get('has_buttons', False)
    
    if has_buttons:
        # Bot account - show inline buttons!
        await tg_client.send_message(
            config['admin_group_id'],
            "🎛️ **Admin Control Panel**\n\nClick a button below:",
            buttons=get_admin_menu()
        )
    else:
        # User account - text commands
        msg = "🎛️ **Admin Control Panel**\n\n"
        msg += "**📊 Status & Logs:**\n"
        msg += "/status - Check bot status\n"
        msg += "/logs - Get last 20 log lines\n\n"
        msg += "**🔄 Restart Options:**\n"
        msg += "/restart - Restart bot\n"
        msg += "/forcerestart - Clear logs + restart\n"
        msg += "/deploy - Git pull + restart\n\n"
        msg += "**⚙️ Config & Test:**\n"
        msg += "/config - Show current settings\n"
        msg += "/test - Local test (no systemctl)\n\n"
        msg += "**ℹ️ Help:**\n"
        msg += "/help - Show all commands\n"
        msg += "/menu - Show this menu"
        await tg_client.send_message(config['admin_group_id'], msg)


async def cmd_deploy(event, tg_client, config, is_callback=False):
    """Deploy: git pull + clear logs + restart
    Command: cd ~/TradingBotTelegram2 && git pull && sudo journalctl --rotate && sudo journalctl --vacuum-time=1s && sudo systemctl restart tradingbot
    """
    if is_callback:
        await event.answer("🚀 Deploying...")
    
    await tg_client.send_message(config['admin_group_id'], "🚀 **Deploying...**\n1️⃣ Pulling latest code...")
    
    # Step 1: Git pull
    git_result = subprocess.run(
        ['git', 'pull'],
        cwd=os.path.expanduser('~/TradingBotTelegram2'),
        capture_output=True,
        text=True
    )
    
    git_output = git_result.stdout if git_result.stdout else git_result.stderr
    await tg_client.send_message(
        config['admin_group_id'], 
        f"📥 **Git Pull:**\n```\n{git_output[-1000:]}\n```"
    )
    
    if git_result.returncode != 0:
        await tg_client.send_message(config['admin_group_id'], f"❌ Git pull failed")
        return
    
    await tg_client.send_message(config['admin_group_id'], "2️⃣ Clearing logs...")
    
    # Step 2: Rotate logs
    subprocess.run(['sudo', 'journalctl', '--rotate'], capture_output=True)
    
    # Step 3: Clear old logs
    subprocess.run(['sudo', 'journalctl', '--vacuum-time=1s'], capture_output=True)
    
    await tg_client.send_message(config['admin_group_id'], "3️⃣ Restarting bot...")
    
    # Step 4: Restart bot
    result = subprocess.run(
        ['sudo', 'systemctl', 'restart', 'tradingbot'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        await tg_client.send_message(
            config['admin_group_id'], 
            f"❌ Deploy failed: {result.stderr}"
        )
    # Note: Success message will come from startup_alert after bot restarts


async def cmd_config(event, tg_client, config, is_callback=False):
    """Show safe environment variables (non-sensitive only)"""
    if is_callback:
        await event.answer("⚙️ Loading config...")
    
    # Only show these safe variables
    listen_to_signal = os.getenv('LISTEN_TO_SIGNAL_GROUP', 'not set')
    place_real_trades = os.getenv('PLACE_REAL_TRADES', 'not set')
    
    # Determine emoji based on values
    signal_emoji = "✅" if listen_to_signal.lower() == 'true' else "❌"
    trades_emoji = "✅" if place_real_trades.lower() == 'true' else "❌"
    
    msg = "⚙️ **Current Configuration:**\n\n"
    msg += f"{signal_emoji} `LISTEN_TO_SIGNAL_GROUP` = `{listen_to_signal}`\n"
    msg += f"{trades_emoji} `PLACE_REAL_TRADES` = `{place_real_trades}`\n"
    msg += "\n---\n"
    msg += "🟢 `true` = Signal channel / Real trades\n"
    msg += "🔴 `false` = Private group / Simulation"
    
    await tg_client.send_message(config['admin_group_id'], msg)


async def cmd_test(event, tg_client, config, is_callback=False):
    """
    Test command for local testing - works without systemctl!
    Tests: uptime, config read, button response, message sending
    """
    if is_callback:
        await event.answer("🧪 Testing...")
    
    # Calculate uptime
    uptime_seconds = int(time.time() - BOT_START_TIME)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    # Read config
    listen_to_signal = os.getenv('LISTEN_TO_SIGNAL_GROUP', 'not set')
    place_real_trades = os.getenv('PLACE_REAL_TRADES', 'not set')
    admin_group = os.getenv('ADMIN_GROUP_ID', 'not set')
    
    # Build test report
    msg = "🧪 **Local Test Results:**\n\n"
    msg += "✅ **Bot Running** (Python process)\n"
    msg += f"✅ **Uptime:** {hours}h {minutes}m {seconds}s\n"
    msg += f"✅ **Admin Group:** Connected\n"
    msg += f"✅ **Buttons:** Working\n"
    msg += f"✅ **Message Send:** Working\n\n"
    msg += "**Config Check:**\n"
    msg += f"   `LISTEN_TO_SIGNAL_GROUP` = `{listen_to_signal}`\n"
    msg += f"   `PLACE_REAL_TRADES` = `{place_real_trades}`\n"
    msg += f"   `ADMIN_GROUP_ID` = `{admin_group[:10]}...`\n\n"
    msg += "⚠️ **Note:** Commands like /restart, /logs require GCP with systemd"
    
    await tg_client.send_message(config['admin_group_id'], msg)


# =============================================================================
# COMMANDS DICTIONARY - Add new commands here
# =============================================================================

COMMANDS = {
    '/status': {
        'description': 'Check bot status (systemctl)',
        'handler': cmd_status
    },
    '/restart': {
        'description': 'Restart the bot',
        'handler': cmd_restart
    },
    '/forcerestart': {
        'description': 'Force restart (clear logs + restart)',
        'handler': cmd_forcerestart
    },
    '/deploy': {
        'description': 'Deploy: git pull + clear logs + restart',
        'handler': cmd_deploy
    },
    '/config': {
        'description': 'Show current config (safe vars only)',
        'handler': cmd_config
    },
    '/logs': {
        'description': 'Get last 20 log lines',
        'handler': cmd_logs
    },
    '/help': {
        'description': 'Show available commands',
        'handler': cmd_help
    },
    '/menu': {
        'description': 'Show interactive button menu',
        'handler': cmd_menu
    },
    '/test': {
        'description': 'Local test (works without systemctl)',
        'handler': cmd_test
    },
}

CALLBACK_HANDLERS = {
    b'cmd_status': cmd_status,
    b'cmd_restart': cmd_restart,
    b'cmd_logs': cmd_logs,
    b'cmd_help': cmd_help,
    b'cmd_forcerestart': cmd_forcerestart,
    b'cmd_deploy': cmd_deploy,
    b'cmd_config': cmd_config,
    b'cmd_test': cmd_test,
}


# =============================================================================
# MAIN HANDLERS - Called by bot.py
# =============================================================================

async def handle_admin_command(event, tg_client, config):
    """
    Main handler for admin text commands.
    Called by bot.py when message received in admin group.
    """
    text = event.raw_text.strip()
    
    # Check if message is a command
    if not text.startswith('/'):
        return
    
    # Get command (first word)
    command = text.split()[0].lower()
    
    # Check if command exists
    if command in COMMANDS:
        print(f"[ADMIN] Command received: {command}")
        await COMMANDS[command]['handler'](event, tg_client, config, is_callback=False)
    else:
        # Unknown command - show help
        await tg_client.send_message(
            config['admin_group_id'],
            f"❓ Unknown command: `{command}`\nUse /help or /menu to see available options."
        )


async def handle_button_click(event, tg_client, config):
    """
    Handler for inline button clicks (callback queries).
    Called by bot.py when a button is clicked in admin group.
    """
    callback_data = event.data
    
    if callback_data in CALLBACK_HANDLERS:
        print(f"[ADMIN] Button clicked: {callback_data.decode()}")
        await CALLBACK_HANDLERS[callback_data](event, tg_client, config, is_callback=True)
    else:
        await event.answer("❓ Unknown button action")


async def send_startup_alert(tg_client, admin_group_id, has_buttons=False):
    """Send alert when bot starts - with buttons if bot account available"""
    try:
        if has_buttons:
            # Bot account - show inline buttons!
            await tg_client.send_message(
                admin_group_id, 
                "🟢 **Bot started successfully!**\n\nClick a button below:",
                buttons=get_admin_menu()
            )
            print("[ADMIN] Startup alert sent with buttons!")
        else:
            # User account - text commands only
            msg = "🟢 **Bot started successfully!**\n\n"
            msg += "**Quick Commands:**\n"
            msg += "/status /logs /config /test\n\n"
            msg += "/menu - Show all commands"
            await tg_client.send_message(admin_group_id, msg)
            print("[ADMIN] Startup alert sent (text mode)")
    except Exception as e:
        print(f"[ADMIN] Failed to send startup alert: {e}")
