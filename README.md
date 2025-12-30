# 🤖 Telegram Trading Signal Bot

Automatically execute Binance Futures trades based on signals received from a Telegram channel.

## 📊 How It Works

```mermaid
flowchart LR
    A[📱 Signal Channel] -->|New Message| B[🤖 Bot]
    B -->|Parse Signal| C{Extract Data}
    C -->|Symbol, Side, Price, TP| D[📈 Binance API]
    D -->|Place Orders| E[✅ Entry + TP Order]
    B -->|Notify| F[👤 Your Private Group]
```

### Flow Explanation

| Step | What Happens |
|------|--------------|
| 1️⃣ | Signal arrives in **Signal Channel** (public/private channel you're monitoring) |
| 2️⃣ | Bot parses the message → extracts Symbol, Side (Long/Short), Price, TP1 |
| 3️⃣ | Bot places **Entry Order** + **Take Profit Order** on Binance Futures |
| 4️⃣ | Bot sends confirmation (or error) to **Your Private Group** |

> **Result:** You get notified in your private group about every trade! 🚀

## 📁 Project Structure

```
ShantoohBot2/
├── bot.py              # Main bot logic
├── generate_session.py # Run once to get SESSION_STRING
├── requirements.txt    # Python dependencies
├── .env                # API keys & config (template on GitHub, real values local only)
├── .gitignore          # Excludes sensitive files
└── README.md           # This file
```

## ⚙️ Configuration

Create a `.env` file with your credentials:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
SESSION_STRING=your_session_string
BINANCE_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret
SIGNAL_CHANNEL_ID=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID=-100xxxxxxxxxx
LEVERAGE=5
MARGIN_USD=100

# Testing Configuration (2 simple variables)
LISTEN_TO_PRIVATE_GROUP=true
PLACE_REAL_TRADES=false
```

### Testing Modes:

| LISTEN_TO_PRIVATE_GROUP | PLACE_REAL_TRADES | Use Case |
|-------------------------|-------------------|----------|
| `true` | `false` | Test signal parsing (no trades) |
| `true` | `true` | Test with real trades from private group |
| `false` | `false` | Monitor signal channel (no trades) |
| `false` | `true` | 🚀 **PRODUCTION** - Real trades from signal channel |

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

The bot parses signals in this format:

```
#COINNAME | Open Long
Current price: 0.02926
TP 1: 0.029556 - Probability 94%
...
```

**Extracted Data:**
| Field | Example | Usage |
|-------|---------|-------|
| Symbol | `#CUDIS` → `CUDISUSDT` | Trading pair |
| Side | `Open Long` → `BUY` | Order direction |
| Price | `0.02926` | Limit order price |
| TP1 | `0.029556` | Take profit price |

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
# Restart bot after any changes
sudo systemctl restart tradingbot

# View live logs (Ctrl+C to exit)
sudo journalctl -u tradingbot -f
```

**All Commands:**

| Command | Purpose |
|---------|---------|
| `sudo systemctl status tradingbot` | Check if running |
| `sudo systemctl restart tradingbot` | Restart bot |
| `sudo systemctl stop tradingbot` | Stop bot |
| `sudo systemctl start tradingbot` | Start bot |
| `sudo journalctl -u tradingbot -f` | View live logs |
| `sudo journalctl -u tradingbot -n 50` | Last 50 log lines |
| `nano ~/TradingBotTelegram2/.env` | Edit config |

---

### Updating Bot Code on VM

When you push changes to GitHub, update the VM:

```bash
# SSH into VM, then:
cd ~/TradingBotTelegram2
git pull origin main
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
- To be safe: Set up **Budget Alerts** in GCP Console → Billing → Budgets

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

## ⚠️ Disclaimer

This bot executes real trades. Use at your own risk. Always test with small amounts first.

---

## 👨‍💻 Author

**Abhijit Gawai**

*✨ Vibe coded with [Antigravity](https://deepmind.google/) using Claude Opus 4.5 Thinking*

