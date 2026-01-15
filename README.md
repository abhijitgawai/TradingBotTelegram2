# 🤖 Telegram Trading Signal Bot

Automatically execute Binance Futures trades based on signals received from **multiple Telegram channels**.

## 📊 How It Works

```mermaid
flowchart LR
    subgraph Signal Channels
        A1[📱 Signal Channel BOT_1_P]
        A2[📱 Signal Channel BOT_2_BK]
        A3[📱 Signal Channel BOT_3_GG]
    end
    
    A1 -->|New Message| B[🤖 bot.py]
    A2 -->|New Message| B
    A3 -->|New Message| B
    
    B -->|Parse| C1[BOT_1_P.py]
    B -->|Parse| C2[BOT_2_BK.py]
    B -->|Parse| C3[BOT_3_GG.py]
    
    C1 -->|Symbol, Side, Price, TP| D[📈 Binance API]
    C2 -->|Symbol, Side, Price, TP, SL| D
    C3 -->|Symbol, Side, Price, TP, SL| D
    
    D -->|Place Orders| E[✅ Entry + TP + SL]
    
    B -->|Notify| F1[👤 Private Group BOT_1_P]
    B -->|Notify| F2[👤 Private Group BOT_2_BK]
    B -->|Notify| F3[👤 Private Group BOT_3_GG]
```

### Flow Explanation

| Step | What Happens |
|------|--------------|
| 1️⃣ | Signal arrives in **Signal Channel** (BOT_1_P, BOT_2_BK, or BOT_3_GG) |
| 2️⃣ | `bot.py` routes to correct parser (BOT_1_P.py, BOT_2_BK.py, or BOT_3_GG.py) |
| 3️⃣ | Parser extracts Symbol, Side (Long/Short), Price, TP1, (SL for BOT_2_BK/BOT_3_GG) |
| 4️⃣ | Bot places **Entry Order** + **Take Profit Order** + **Stop Loss** on Binance Futures |
| 5️⃣ | Bot sends confirmation (or error) to corresponding **Private Group** |

> **Result:** Each signal channel has its own private group for notifications! 🚀

## 📁 Project Structure

```
TradingBotTelegram2/
├── bot.py              # Main bot - runs BOT_1_P, BOT_2_BK, BOT_3_GG
├── BOT_1_P.py          # Parser for Signal Channel P (no SL)
├── BOT_2_BK.py         # Parser for Signal Channel BK (has SL)
├── BOT_3_GG.py         # Parser for Signal Channel GG (has SL + Entry Zone)
├── ADMIN_BOT.py        # Admin commands with inline buttons
├── verify_setup.py     # Test suite - verify all connections
├── generate_session.py # Run once to get SESSION_STRING
├── requirements.txt    # Python dependencies
├── .env                # API keys & config (not in git)
├── .gitignore          # Excludes sensitive files
└── README.md           # This file
```

## ⚙️ Configuration

Create a `.env` file with your credentials:

```env
# --- Telegram Credentials ---
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
SESSION_STRING=your_session_string

# --- Binance Credentials ---
BINANCE_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret

# --- Testing Switches ---
LISTEN_TO_SIGNAL_GROUP=true
PLACE_REAL_TRADES=false

# --- BOT 1 (Channel P) Config ---
SIGNAL_CHANNEL_ID_BOT_1_P=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_1_P=-xxxxxxxxxx
LEVERAGE_BOT_1_P=5
MARGIN_USD_BOT_1_P=100

# --- BOT 2 (Channel BK) Config ---
SIGNAL_CHANNEL_ID_BOT_2_BK=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_2_BK=-xxxxxxxxxx
LEVERAGE_BOT_2_BK=5
MARGIN_USD_BOT_2_BK=100

# --- BOT 3 (Channel GG) Config ---
SIGNAL_CHANNEL_ID_BOT_3_GG=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_3_GG=-xxxxxxxxxx
LEVERAGE_BOT_3_GG=5
MARGIN_USD_BOT_3_GG=100

# --- Admin Bot Config (for inline buttons) ---
ADMIN_GROUP_ID=-100xxxxxxxxxx
ADMIN_BOT_TOKEN=your_bot_token_from_botfather
```

### Variable Reference:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_API_ID` | Your Telegram app ID from my.telegram.org |
| `TELEGRAM_API_HASH` | Your Telegram app hash |
| `SESSION_STRING` | Generated once using `generate_session.py` |
| `BINANCE_KEY` | Binance API key (enable Futures, disable Withdraw) |
| `BINANCE_SECRET` | Binance API secret |
| `LISTEN_TO_SIGNAL_GROUP` | `true` = listen to signal channels, `false` = private groups |
| `PLACE_REAL_TRADES` | `true` = real orders, `false` = simulation |
| `SIGNAL_CHANNEL_ID_BOT_1_P` | Signal channel ID for BOT_1_P |
| `MY_PRIVATE_GROUP_ID_BOT_1_P` | Private group for BOT_1_P notifications |
| `LEVERAGE_BOT_1_P` | Leverage for BOT_1_P trades |
| `MARGIN_USD_BOT_1_P` | Margin in USD per trade for BOT_1_P |
| `SIGNAL_CHANNEL_ID_BOT_2_BK` | Signal channel ID for BOT_2_BK |
| `MY_PRIVATE_GROUP_ID_BOT_2_BK` | Private group for BOT_2_BK notifications |
| `LEVERAGE_BOT_2_BK` | Leverage for BOT_2_BK trades |
| `MARGIN_USD_BOT_2_BK` | Margin in USD per trade for BOT_2_BK |
| `ADMIN_GROUP_ID` | Telegram supergroup ID for admin commands |
| `ADMIN_BOT_TOKEN` | Bot token from @BotFather (for inline buttons) |

### Testing Modes:

| LISTEN_TO_SIGNAL_GROUP | PLACE_REAL_TRADES | Use Case |
|------------------------|-------------------|----------|
| `false` | `false` | Test signal parsing from private group (no trades) |
| `false` | `true` | Test with real trades from private group |
| `true` | `false` | Monitor signal channel (no trades) |
| `true` | `true` | 🚀 **PRODUCTION** - Real trades from signal channel |

### Isolated Margin Setup (One-Time):

```env
# Set to true to pre-configure ALL Binance symbols to ISOLATED margin mode
RUN_ISOLATED_SCRIPT=false
```

When `RUN_ISOLATED_SCRIPT=true`, running `python verify_setup.py` will:
1. Fetch all 600+ PERPETUAL symbols from Binance
2. Set each one to ISOLATED margin mode (with rate limiting)
3. Takes ~10 minutes to complete

**Why?** ISOLATED mode is safer - only position margin is at risk, not your entire account.

> Run this **once** before deploying. After completion, set back to `false`.

---

## 📋 Step-by-Step Setup Guide

### Step 1: Get Telegram API Credentials

1. Go to **https://my.telegram.org**
2. Login with phone number (with country code: `+919876543210`)
3. Enter OTP received in Telegram
4. Click **"API development tools"**
5. Fill form:
   - App title: `TradingBot`
   - Short name: `tradingbot`
   - Platform: `Desktop`
   - URL: (leave empty)
6. Click **Create application**
7. Copy `App api_id` → `TELEGRAM_API_ID`
8. Copy `App api_hash` → `TELEGRAM_API_HASH`

> **Note:** FCM credentials are NOT needed.

---

### Step 2: Get Binance API Credentials

1. Go to **https://www.binance.com** → Login
2. Profile → **API Management**
3. Click **Create API** → Select **System generated**
4. Label: `TradingBot` → Complete 2FA
5. Copy `API Key` → `BINANCE_KEY`
6. Copy `Secret Key` → `BINANCE_SECRET` (shown once!)
7. **Edit Restrictions:**
   - ✅ Enable Futures
   - ✅ Enable Reading
   - ❌ Disable Withdraw (for safety)

#### ⚠️ IP Restriction (Required for Futures)

Binance requires IP whitelist when Futures is enabled. Add your IP:

**For Local Testing:**
```bash
# Windows - Get your public IP
curl ifconfig.me

# Or visit: https://whatismyip.com
```

Copy your public IP (e.g., `103.45.67.89`) and add it to Binance API restrictions.

**For Cloud Deployment:**
- Use your GCP VM's static IP (see deployment section below)

---

### Step 3: Get Channel/Group IDs

**Using Telegram Web (Recommended)**
1. Open https://web.telegram.org/a/
2. Go to the channel/group
3. Look at URL: `https://web.telegram.org/a/#-1001234567890`
4. Copy the number after `#` (including the minus sign)

| ID Type | URL Example | Use in .env |
|---------|-------------|-------------|
| Channel | `#-1001234567890` | `-1001234567890` |
| Group | `#-5160897944` | `-1005160897944` |

---

### Step 4: Generate Session String

```bash
# 1. First fill TELEGRAM_API_ID and TELEGRAM_API_HASH in .env
# 2. Run:
python generate_session.py

# 3. Copy the output and paste into SESSION_STRING in .env
```

---

## 🚀 Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python bot.py
```

---

## 📡 Signal Format

### BOT_1_P (Channel P) - No Stop Loss

```
#COINNAME | Open Long
Current price: 0.02926
TP 1: 0.029556 - Probability 94%
```

| Field | Pattern | Example |
|-------|---------|---------|
| Symbol | `#COINNAME` | `#DOGE` → `DOGEUSDT` |
| Side | `Open Long` / `Open Short` | `Open Long` → `BUY` |
| Entry | `Current price: X.XXX` | `0.02926` |
| TP1 | `TP 1: X.XXX` | `0.029556` |

### BOT_2_BK (Channel BK) - Has Stop Loss

```
#COINNAME/USDT
🟢 LONG (or 🔴 SHORT)
Entry: 0.06527 - 0.06300
Leverage: 20x
Target 1: 0.06592
StopLoss: 0.06180
```

| Field | Pattern | Example |
|-------|---------|---------|
| Symbol | `#COINNAME/USDT` | `#GMT` → `GMTUSDT` |
| Side | `LONG` / `SHORT` | `LONG` → `BUY` |
| Entry | `Entry: X.XXX` (first number) | `0.06527` |
| TP1 | `Target 1: X.XXX` | `0.06592` |
| SL | `StopLoss: X.XXX` | `0.06180` |

### BOT_3_GG (Channel GG) - Has Entry Zone + Stop Loss

```
📩 #DYDXUSDT 30m | Mid-Term
📈 Long Entry Zone: 0.175-0.170
Target 1:  0.177
❌Stop-Loss: 0.168
```

| Field | Pattern | Example |
|-------|---------|---------|
| Symbol | `#COINUSDT` | `#DYDXUSDT` → `DYDXUSDT` |
| Side | `📈 Long Entry Zone` / `📉 Short Entry Zone` | `Long` → `BUY` |
| Entry | First number in Entry Zone | `0.175` |
| TP1 | `Target 1: X.XXX` | `0.177` |
| SL | `❌Stop-Loss: X.XXX` | `0.168` |

---

## 🌐 Deployment on Google Cloud Platform (FREE!)

### Why Google Cloud?
- ✅ **Static IP** (required for Binance API whitelist)
- ✅ **$300 free credits** for 90 days
- ✅ **Always Free tier** after credits
- ✅ **UPI payment** accepted in India (₹1000 refundable deposit)

---

### Step 1: Create Google Cloud Account

1. Go to **https://cloud.google.com/free**
2. Click **"Get started for free"**
3. Sign in with Google account
4. Payment: Select **UPI** → Pay ₹1000 (refundable deposit)
5. Get **$300 free credits**!

---

### Step 2: Create VM Instance

1. Go to **https://console.cloud.google.com**
2. Search **"Compute Engine"** → Click it → Enable API
3. Click **"Create Instance"**

#### VM Configuration (Lowest Cost - FREE!):

| Section | Field | Value |
|---------|-------|-------|
| **Name** | Name | `trading-bot` |
| **Region** | Region | `asia-south1 (Mumbai)` |
| **Region** | Zone | `asia-south1-a` |
| **Machine** | Machine family | `General-purpose` |
| **Machine** | Series | `E2` |
| **Machine** | Machine type | `e2-micro` (2 vCPU, 1 GB) ✅ FREE |
| **Machine** | Provisioning model | `Standard` |
| **OS & Storage** | Operating System | `Ubuntu` |
| **OS & Storage** | Version | `Ubuntu 22.04 LTS x86/64` |
| **OS & Storage** | Boot disk type | `Standard persistent disk` |
| **OS & Storage** | Size | `30 GB` |
| **Networking** | Allow HTTP traffic | ✅ Checked |
| **Networking** | Allow HTTPS traffic | ✅ Checked |
| **Networking** | Allow Load Balancer | ❌ Unchecked |
| **Observability** | Install Ops Agent | ❌ Unchecked (optional) |
| **Advanced** | Deletion protection | ✅ Enabled (recommended) |

4. Click **"Create"** → Wait 1-2 minutes

---

### Step 3: Reserve Static IP (IMPORTANT!)

1. Go to **VPC Network → IP addresses**
2. Click **"Reserve external"**
3. Fill:
   - Name: `trading-bot-ip`
   - Region: `asia-south1`
   - Attached to: `trading-bot` (your VM)
4. Click **"Reserve"**
5. Note your IP (e.g., `34.100.182.165`) ← **This will never change!**

---

### Step 4: Add IP to Binance Whitelist

1. Go to **Binance → API Management**
2. Click **Edit** on your API key
3. Under **IP Access Restrictions** → Add your GCP IP (e.g., `34.100.182.165`)
4. Save

---

### Step 5: Connect to VM via SSH

1. Go to **Compute Engine → VM instances**
2. Find your VM → Click **"SSH"** button
3. A terminal opens in your browser!

---

### Step 6: Setup Bot on VM

Run these commands:

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python, venv & Git
sudo apt install python3 python3-pip python3-venv python3-full git -y

# 3. Clone your code
git clone https://github.com/YOUR_USERNAME/ShantoohBot2.git
cd ShantoohBot2

# 4. Create virtual environment
python3 -m venv venv

# 5. Activate virtual environment
source venv/bin/activate

# 6. Install dependencies (inside venv)
pip install -r requirements.txt

# 7. Create .env file
nano .env
# (Paste your secrets, then Ctrl+X → Y → Enter)

# 8. Test the bot
python bot.py
# Should show: "🚀 PRODUCTION MODE: Listening..."
# Press Ctrl+C to stop
```

> **Note:** Always activate venv with `source venv/bin/activate` before running the bot!

---

### Step 7: Run Bot 24/7 (Systemd Service)

**First, find your username:**
```bash
whoami
# Example output: abhijeetgawai2000
```

**Create service file:**
```bash
sudo nano /etc/systemd/system/tradingbot.service
```

**Paste this (replace `abhijeetgawai2000` with YOUR username from `whoami`):**
```ini
[Unit]
Description=Trading Bot
After=network.target

[Service]
# CHANGE THIS: Replace 'abhijeetgawai2000' with your username from 'whoami' command
User=abhijeetgawai2000
WorkingDirectory=/home/abhijeetgawai2000/TradingBotTelegram2
ExecStart=/home/abhijeetgawai2000/TradingBotTelegram2/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Save:** `Ctrl+X` → `Y` → `Enter`

**Start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable tradingbot
sudo systemctl start tradingbot
sudo systemctl status tradingbot
```

---

### Useful Commands

**Most Used (copy-paste ready):**
```bash
# Restart bot and view live logs
sudo systemctl restart tradingbot && sudo journalctl -u tradingbot -f
```

**All Systemd Commands:**

| Command | Purpose |
|---------|---------|
| `sudo systemctl status tradingbot` | Check if running |
| `sudo systemctl restart tradingbot` | Restart bot |
| `sudo systemctl stop tradingbot` | Stop bot |
| `sudo systemctl start tradingbot` | Start bot |
| `sudo systemctl enable tradingbot` | Enable auto-start on boot |
| `sudo systemctl disable tradingbot` | Disable auto-start |
| `sudo systemctl daemon-reload` | Reload service file after editing |

**Log Commands:**

| Command | Purpose |
|---------|---------|
| `sudo journalctl -u tradingbot -f` | View live logs (follow mode) |
| `sudo journalctl -u tradingbot -n 50` | Last 50 log lines |
| `sudo journalctl -u tradingbot -n 100 --no-pager` | Last 100 lines without paging |
| `sudo journalctl -u tradingbot --since "1 hour ago"` | Logs from last hour |
| `sudo journalctl -u tradingbot --since today` | Today's logs |
| `sudo journalctl -u tradingbot -p err` | Error logs only |

**File Editing:**

| Command | Purpose |
|---------|---------|
| `nano ~/TradingBotTelegram2/.env` | Edit config |
| `cat ~/TradingBotTelegram2/.env` | View config |
| `sudo nano /etc/systemd/system/tradingbot.service` | Edit service file |
| `sudo cat /etc/systemd/system/tradingbot.service` | View service file |

**Combined Commands:**

```bash
# Stop bot, pull latest code, restart
sudo systemctl stop tradingbot && cd ~/TradingBotTelegram2 && git pull && sudo systemctl start tradingbot

# Restart and immediately check status
sudo systemctl restart tradingbot && sudo systemctl status tradingbot

# View last 20 lines then follow live
sudo journalctl -u tradingbot -n 20 -f
```

---

### Updating Bot Code on VM

When you push changes to GitHub, update the VM:

```bash
# 1. Go to project folder
cd ~/TradingBotTelegram2

# 2. Backup .env and stash local changes (avoids merge conflicts)
cp .env .env.backup
git stash

# 3. Pull latest code
git pull origin main

# 4. Restore your real .env
cp .env.backup .env

# 5. Restart bot
sudo systemctl restart tradingbot
sudo journalctl -u tradingbot -f
```

### Running verify_setup.py on VM

You can run the test script while bot is running (separate process):

```bash
cd ~/TradingBotTelegram2
source venv/bin/activate

# Edit .env to set RUN_ISOLATED_SCRIPT=true (if needed)
nano .env

# Run tests
python verify_setup.py

# Restart bot after tests
sudo systemctl restart tradingbot
```

### After Changing Files - What To Do?

**You DON'T need to redo systemd setup!** Just restart:

| What You Changed | Commands to Run |
|------------------|-----------------|
| `.env` file | `sudo systemctl restart tradingbot` |
| `bot.py` (pushed to GitHub) | `git pull origin main` then `sudo systemctl restart tradingbot` |
| `bot.py` (edited directly on VM) | `sudo systemctl restart tradingbot` |
| `tradingbot.service` file | `sudo systemctl daemon-reload` then `sudo systemctl restart tradingbot` |

**Quick restart:**
```bash
sudo systemctl restart tradingbot && sudo systemctl status tradingbot
```

---

### Git Tips for .env Security

**Keep template on GitHub, real values local only:**

```bash
# Stop Git from tracking local .env changes
git update-index --assume-unchanged .env

# To undo (if you want to update the template):
git update-index --no-assume-unchanged .env
```

This way:
- GitHub has mock/template `.env` 
- Your local `.env` has real keys (not tracked)
- GCP VM has real keys (created manually)

---

### Cost Summary

| Component | Monthly Cost |
|-----------|--------------|
| e2-micro VM (744 hrs) | **$0** (free tier) |
| 30 GB Standard disk | ~$1.20 |
| Static IP (attached) | **$0** |
| **Total** | ~$1.20/month (covered by $300 credits for 250 months!) |

### 💳 Billing & Payment Notes

**Q: I paid ₹1000 via UPI and deleted the autopay. Will I be charged?**

| Scenario | What Happens |
|----------|--------------|
| Stay within free tier | ✅ No charges, ₹1000 stays as credit |
| Use only free resources | ✅ Safe, no deductions |
| Exceed free tier | ⚠️ Google emails you, service pauses (no surprise charges) |
| Delete payment method | ✅ OK if staying in free tier |

**Important:**
- Your ₹1000 deposit is converted to ~$12 credit (added to $300 free credits)
- Google **cannot charge you** without a valid payment method
- If you exceed limits, service pauses - you won't be billed unexpectedly
---

## 🚀 GCP Quick Start - All Commands (Copy-Paste Ready)

Complete command reference for first-time setup and daily operations on GCP VM.

### Your VM Details

| Property | Value |
|----------|-------|
| **VM Name** | `tradingbottelegram2` |
| **Zone** | `asia-south1-a` |
| **Machine Type** | `e2-micro` |
| **External IP** | `xx.xx.xx.xx` |

### SSH Into Your VM

```bash
# From your local machine (run this first!)
gcloud compute ssh tradingbottelegram2 --zone=asia-south1-a
```

> **Tip:** If you get authentication errors, run `gcloud auth login` first.

---

### First-Time Setup (Run Once)

```bash
# ============================================
# STEP 1: System Update & Package Installation
# ============================================
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv python3-full git -y

# ============================================
# STEP 2: Clone Repository
# ============================================
# Using HTTPS (recommended for beginners)
git clone https://github.com/abhijitgawai/TradingBotTelegram2.git
cd TradingBotTelegram2

# OR using SSH (if you have SSH keys setup)
# git clone git@github.com:abhijitgawai/TradingBotTelegram2.git
# cd TradingBotTelegram2

# ============================================
# STEP 3: Create & Activate Virtual Environment
# ============================================
python3 -m venv venv
source venv/bin/activate

# ============================================
# STEP 4: Install Python Dependencies
# ============================================
pip install -r requirements.txt

# ============================================
# STEP 5: Create .env File with Real Credentials
# ============================================
nano .env
# Paste your credentials, then save: Ctrl+X → Y → Enter

# ============================================
# STEP 6: Test Bot Manually (Optional)
# ============================================
python bot.py
# Press Ctrl+C to stop after testing

# ============================================
# STEP 7: Find Your Username (for systemd)
# ============================================
whoami
# Note the output (e.g., abhijeetgawai2000)

# ============================================
# STEP 8: Create Systemd Service File
# ============================================
sudo nano /etc/systemd/system/tradingbot.service

# Paste this (replace USERNAME with your username from whoami):
# [Unit]
# Description=Trading Bot
# After=network.target
#
# [Service]
# User=USERNAME
# WorkingDirectory=/home/USERNAME/TradingBotTelegram2
# ExecStart=/home/USERNAME/TradingBotTelegram2/venv/bin/python bot.py
# Restart=always
# RestartSec=10
# Environment=PYTHONUNBUFFERED=1
#
# [Install]
# WantedBy=multi-user.target

# Save: Ctrl+X → Y → Enter

# ============================================
# STEP 9: Enable & Start Service
# ============================================
sudo systemctl daemon-reload
sudo systemctl enable tradingbot
sudo systemctl start tradingbot
sudo systemctl status tradingbot
```

---

### Daily Operations

```bash
# View live logs
sudo journalctl -u tradingbot -f

# Restart bot
sudo systemctl restart tradingbot

# Stop bot
sudo systemctl stop tradingbot

# Start bot
sudo systemctl start tradingbot

# Check status
sudo systemctl status tradingbot
```

---

### Update Code from GitHub

```bash
# Navigate to project
cd ~/TradingBotTelegram2

# Backup .env
cp .env .env.backup

# Pull latest changes
git stash
git pull origin main

# Restore .env
cp .env.backup .env

# Restart bot
sudo systemctl restart tradingbot

# View logs
sudo journalctl -u tradingbot -f
```

---

### If Repo is Private (Authentication Required)

If you made your GitHub repo private, you need to set up a **Personal Access Token (PAT)** for git pull to work on GCP.

#### Step 1: Generate Personal Access Token on GitHub

1. Go to **GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Name: `TradingBotTelegram2`
4. Expiration: `90 days` (recommended)
5. Scope: ✅ **repo** (check this box)
6. Click **Generate token**
7. **Copy the token immediately** (starts with `ghp_...`) - you won't see it again!

#### Step 2: Update Remote URL on GCP VM

SSH into your VM and run this command (replace `YOUR_TOKEN` with your actual token):

```bash
cd ~/TradingBotTelegram2
git remote set-url origin https://abhijitgawai:YOUR_TOKEN@github.com/abhijitgawai/TradingBotTelegram2.git
```

**Example:**
```bash
git remote set-url origin https://abhijitgawai:ghp_abc123xyz789@github.com/abhijitgawai/TradingBotTelegram2.git
```

#### Step 3: Now Git Pull Works!

```bash
git pull
```

> **Security Notes:**
> - Token is stored in `.git/config` on your private VM (safe)
> - Set an expiration date on the token
> - You can revoke the token anytime from GitHub settings
> - When token expires, generate a new one and repeat Step 2

---

### One-Liner Commands

```bash
# Update & restart (most common)
cd ~/TradingBotTelegram2 && git pull && sudo systemctl restart tradingbot && sudo journalctl -u tradingbot -f

# Restart and view logs
sudo systemctl restart tradingbot && sudo journalctl -u tradingbot -f

# Stop, update, start
sudo systemctl stop tradingbot && cd ~/TradingBotTelegram2 && git pull && sudo systemctl start tradingbot

# View last 50 logs then follow live
sudo journalctl -u tradingbot -n 50 -f
```

---

### Edit Files on VM

```bash
# Edit .env
nano ~/TradingBotTelegram2/.env

# View .env
cat ~/TradingBotTelegram2/.env

# Edit systemd service
sudo nano /etc/systemd/system/tradingbot.service
# After editing: sudo systemctl daemon-reload && sudo systemctl restart tradingbot
```

---

### Troubleshooting Commands

```bash
# Check if bot process is running
ps aux | grep python

# Check VM's public IP (for Binance whitelist)
curl -s ifconfig.me && echo

# Check disk space
df -h

# Check memory usage
free -h

# View system logs
sudo journalctl -u tradingbot --since "1 hour ago"

# View only error logs
sudo journalctl -u tradingbot -p err

# Kill stuck Python processes (emergency)
pkill -f python
```

---

## 🔧 Binance Futures Settings (IMPORTANT!)

Before running the bot, configure these settings on Binance:

### Position Mode: One-Way Mode

1. Go to **Binance Futures** → **Settings** (gear icon, top right)
2. Find **Position Mode**
3. Select **One-Way Mode** (not Hedge Mode)

> ⚠️ If you see error `"Order's position side does not match user's setting"`, you need to switch to One-Way Mode.

### Margin Mode: Isolated (Recommended)

1. On Binance Futures trading page
2. Click on margin mode (next to leverage)
3. Select **Isolated** (safer than Cross)

| Mode | Risk Level | Description |
|------|------------|-------------|
| Isolated | ✅ Lower | Only position margin is at risk |
| Cross | ⚠️ Higher | Entire account balance at risk |

---

## 🛠️ Troubleshooting Common Errors

### Error: "Precision is over the maximum"
```
⚠️ Binance Error for DOGEUSDT: (400, -1111, 'Precision is over the maximum defined for this asset.')
```
**Cause:** Quantity has too many decimal places for this coin  
**Fix:** Bot now uses smart rounding based on price:

| Price Range | Decimals | Example |
|-------------|----------|---------|
| > $1000 (BTC, ETH) | 3 | `0.050` |
| $1 - $1000 | 1 | `125.5` |
| < $1 (DOGE, SHIB) | 0 | `4065` |

---

### Error: "Position side does not match"
```
⚠️ Binance Error: (400, -4061, "Order's position side does not match user's setting.")
```
**Cause:** Binance is in Hedge Mode  
**Fix:** Switch to **One-Way Mode** in Binance Futures settings (see above)

---

### Error: Git pull conflict on VM
```
error: Pulling is not possible because you have unmerged files.
```
**Cause:** You edited `.env` on VM and Git detects conflict  
**Fix:**
```bash
# Backup your .env
cp .env .env.backup

# Reset and pull
git reset --hard HEAD
git pull origin main

# Restore your real credentials
cp .env.backup .env

# Restart bot
sudo systemctl restart tradingbot
```

---

### Error: "daemon-reload" warning
```
Warning: The unit file of tradingbot.service changed on disk. Run 'systemctl daemon-reload'
```
**Cause:** Service file was modified  
**Fix:** Just run `sudo systemctl daemon-reload` then restart

---

## 📌 Important Notes

### Order Types
The bot places **LIMIT orders** (not market orders):
- **Entry:** Limit order at signal's current price
- **Take Profit:** Limit order at TP1 price with `reduceOnly=True`

### Quantity Calculation
```
Position Size = MARGIN_USD × LEVERAGE
Quantity = Position Size ÷ Entry Price
```
Example with `MARGIN_USD=100`, `LEVERAGE=5`, price `$0.32`:
```
Position = $100 × 5 = $500
Quantity = $500 ÷ $0.32 = 1562 coins
```

### Verifying VM IP
Check if your VM IP matches Binance whitelist:
```bash
curl -s ifconfig.me && echo
```

### Static vs Ephemeral IP
| IP Type | Changes on restart? | Binance compatible? |
|---------|---------------------|---------------------|
| Ephemeral | ⚠️ Yes | ❌ No |
| Static | ✅ No | ✅ Yes |

Always use **Static IP** for Binance API (see Step 3 in deployment).

---

## 🏆 Problems Solved During Development

| Problem | Root Cause | Solution |
|---------|------------|----------|
| **Invalid symbol error** | Typo in coin name (DODGE vs DOGE) | Bot auto-appends USDT, just use correct ticker |
| **Precision over maximum** | Quantity had wrong decimal places | Implemented API-based precision caching at startup |
| **Position side mismatch** | Binance in Hedge Mode | Switch to One-Way Mode in Binance Futures settings |
| **Git pull conflict on VM** | Edited .env on VM caused merge conflict | Use `git reset --hard HEAD` then restore .env from backup |
| **IP not whitelisted** | Local IP not added to Binance | Add both local and GCP VM IPs to whitelist |
| **Cross margin risk** | Default was Cross margin | Added automatic Isolated margin setting via API |
| **Fallback decimals inaccurate** | Price-based estimation failed for some coins | Cache all 655 symbol precisions from Binance at startup |

---

## 📝 Changelog

### v1.3 (Latest)
- ✅ **Symbol precision caching** - Fetches exact decimal places from Binance API at startup
- ✅ **Fallback logic** - Uses price-based estimation if symbol not in cache
- ✅ **Test suite** - Added `verify_setup.py` with 8 comprehensive tests

### v1.2
- ✅ **Isolated margin mode** - Automatically sets each trade to Isolated (safer)
- ✅ **Troubleshooting docs** - Added common errors and fixes to README

### v1.1
- ✅ **Smart quantity rounding** - Dynamic decimals based on coin price
- ✅ **Debug logging** - Detailed console output for signal processing
- ✅ **Telegram ID normalization** - Handles -100XXXXXX format automatically

### v1.0
- ✅ **Core functionality** - Parse signals, place limit orders, send notifications
- ✅ **Testing modes** - LISTEN_TO_PRIVATE_GROUP and PLACE_REAL_TRADES flags
- ✅ **GCP deployment guide** - Step-by-step with static IP and systemd service

---

## ⚠️ Disclaimer

This bot executes real trades. Use at your own risk. Always test with small amounts first.

---

## 👨‍💻 Author

**Abhijit Gawai**

*✨ Vibe coded with [Antigravity](https://deepmind.google/) using Claude Opus 4.5 Thinking*

