# 🤖 Simplus Auto Referral Bot

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Active-brightgreen.svg)](https://github.com/devtint/Simplus_Refer_gen)

> **Automated referral generation bot for Simplus platform using temporary emails**

## 🎯 Purpose

This bot automates the process of generating referrals for your Simplus account by:
- Creating temporary email addresses
- Registering new accounts with your referral code  
- Managing verification codes automatically
- Tracking your referral progress

**Each successful registration counts as a referral to YOUR account, helping you earn rewards and bonuses!**

---

## ⚠️ Important Disclaimer

```
🚨 EDUCATIONAL PURPOSES ONLY 🚨

This project is created strictly for educational and learning purposes.
Users are responsible for:
- Compliance with platform terms of service
- Adherence to local laws and regulations  
- Ethical usage and respect for rate limits
- Understanding potential risks and consequences

The authors are not responsible for any misuse or violations.
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Web Control Panel** | Beautiful dashboard with real-time monitoring |
| 🔐 **Authentication** | Secure login system with session management |
| 🔄 **Automated Email Generation** | Uses mail.tm API for temporary emails |
| 📧 **Smart Verification** | Automatically captures and processes OTP codes |
| 🎫 **Multi-Code Support** | Process multiple referral codes per cycle |
| ⚙️ **Dynamic Configuration** | Manage codes and timings via web UI |
| 📊 **Progress Tracking** | Real-time statistics and success rates |
| 🎛️ **Cycle Management** | Organized in batches with user approval |
| 🔄 **Keep-Alive System** | Prevents Render from sleeping |
| � **Mail.tm Integration** | Direct API for email generation |
| 🛡️ **Error Handling** | Robust error recovery and timeout management |
| 📈 **Live Logs** | Activity logs with color-coded levels |
| ⏸️ **Pause/Resume** | Control bot execution on the fly |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** installed on your system
- **Internet connection** for mail.tm API
- **Stable internet connection**
- **Simplus account** with referral codes

### 1. 📥 Installation

```bash
# Clone the repository
git clone https://github.com/devtint/Simplus_Refer_gen.git
cd Simplus_Refer_gen

# Install dependencies
pip install -r requirements.txt
```

### 2. ⚡ Mail.tm Integration

Uses mail.tm API directly for reliable temporary email generation.

✅ **Benefits:**
- **Fast**: Direct API calls 
- **Reliable**: No external dependencies
- **Simple**: Zero additional setup required
- **Proxy-friendly**: Full HTTP(S) proxy support

### 3. ⚙️ Configuration

**Setup `.env` file**:

```bash
cp .env.example .env
```

**Edit `.env` with your credentials**:

```env
# Required: Your invitation codes (comma-separated)
INVITATION_CODES=CODE1,CODE2,CODE3,CODE4,CODE5

# Required: Web interface credentials
WEB_USERNAME=admin
WEB_PASSWORD=your_secure_password
SECRET_KEY=your-random-secret-key-here

# Optional: Proxy configuration (comma-separated SOCKS5 proxies)
PROXY_LIST=socks5://user:pass@proxy1:1080,socks5://user:pass@proxy2:1080

# Optional: Keep-alive URL for hosting platforms like Render
KEEP_ALIVE_URL=https://your-app-name.onrender.com

# Optional: Country/region settings
NATION_CODE=66
```

> 💡 **Tip**: Generate a secure SECRET_KEY with: `python -c "import secrets; print(secrets.token_hex(32))"`

> 🔒 **Security**: Your `.env` file contains sensitive data and is automatically ignored by git

### 5. 🎮 Run the Bot

**Local Development:**
```bash
python app.py
```

Then visit: `http://localhost:5000`

**Default Login:**
- Username: `admin`
- Password: (whatever you set in `.env`)

### 6. 🌐 Deploy to Render (Production)

#### 📋 Pre-Deployment Checklist

✅ **Complete these steps first:**

1. **Run Verification Script**:
   ```bash
   python setup_check.py
   ```
   Ensure all checks pass before deployment!

2. **Test Locally**:
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000` and verify everything works

3. **Generate Secret Key**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Save this for environment variables

#### 🚀 Step-by-Step Render Deployment

**Step 1: Prepare GitHub Repository**

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

**Step 2: Create Render Web Service**

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select your repository
5. Configure service:
   - **Name**: `simplus-bot` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: `Free`

**Step 3: Configure Environment Variables**

In Render dashboard, go to **"Environment"** tab and add:

```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=+your_phone_number
NATION_CODE=66
INVITATION_CODES=CODE1,CODE2,CODE3,CODE4,CODE5
KEEP_ALIVE_URL=https://your-app-name.onrender.com
WEB_USERNAME=admin
WEB_PASSWORD=your_secure_password
SECRET_KEY=your_generated_secret_key
```

> 📝 **Note**: `KEEP_ALIVE_URL` should be your actual Render app URL (shown after deployment)

**Step 4: Deploy**

1. Click **"Create Web Service"**
2. Wait for build to complete (5-10 minutes)
3. Once deployed, you'll get a URL like: `https://your-app-name.onrender.com`
4. Update `KEEP_ALIVE_URL` environment variable with this URL

**Step 5: Update Keep-Alive URL**

1. Copy your Render app URL
2. Go to **Environment** tab
3. Edit `KEEP_ALIVE_URL` variable
4. Paste your app URL
5. Save changes (app will redeploy automatically)

**Step 6: Setup External Keep-Alive Service**

⚠️ **Important**: Render free tier sleeps after 15 minutes of inactivity!

**Option A: Cron-Job.org (Recommended)**

1. Visit [cron-job.org](https://cron-job.org)
2. Sign up for free account
3. Create new cron job:
   - **Title**: Simplus Bot Keep-Alive
   - **URL**: `https://your-app-name.onrender.com/ping`
   - **Schedule**: Every 5 minutes
   - **Enable**: ✅
4. Save and activate

**Option B: UptimeRobot**

1. Visit [uptimerobot.com](https://uptimerobot.com)
2. Sign up for free account
3. Add new monitor:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Simplus Bot
   - **URL**: `https://your-app-name.onrender.com/ping`
   - **Monitoring Interval**: 5 minutes
4. Create monitor

**Step 7: Access Your Bot**

1. Visit your Render app URL
2. Login with credentials from `WEB_USERNAME` and `WEB_PASSWORD`
3. Go to **Settings** page
4. Configure invitation codes and timing
5. Click **Start Bot** from Dashboard

#### 🔧 Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| **Build Failed** | Check `requirements.txt` syntax, verify Python 3.12 compatibility |
| **Session Error** | Run bot once locally to create `session.session`, then manually upload to Render (not via git) |
| **App Crashes** | Check Render logs, verify all environment variables are set |
| **Can't Login** | Verify `WEB_USERNAME` and `WEB_PASSWORD` environment variables |
| **Bot Sleeps** | Ensure keep-alive is active (check dashboard) and `KEEP_ALIVE_URL` is set correctly |
| **Keep-Alive Red** | Check `KEEP_ALIVE_URL` matches your Render app URL |

#### 📊 Post-Deployment Monitoring

1. **Check Keep-Alive Status**:
   - Dashboard shows green indicator when active
   - Last ping time displayed

2. **Monitor Activity Logs**:
   - Real-time logs on Dashboard
   - Color-coded by severity

3. **Track Success Rate**:
   - Statistics panel updates every 2 seconds
   - Shows current progress and efficiency

4. **Render Logs**:
   - Access via Render dashboard
   - "Logs" tab shows detailed output

---

## 📖 How It Works

```mermaid
graph TD
    A[Start Bot] --> B[Load Configuration]
    B --> C[Initialize mail.tm API]
    C --> D[Generate Temp Email]
    D --> E[Register with Your Referral Code]
    E --> F[Wait for Verification Email]
    F --> G[Extract Verification Code]
    G --> H[Complete Registration]
    H --> I[Success? +1 Referral]
    I --> J{Big Cycle Complete?}
    J -->|No| K[Wait 5 seconds]
    K --> D
    J -->|Yes| L[Show Statistics]
    L --> M[Ask User Approval]
    M -->|Yes| D
    M -->|No| N[Stop Bot]
```

### Process Flow

1. **⚙️ Setup**: Bot loads configuration and initializes mail.tm API
2. **📧 Email Generation**: Creates temporary email address via mail.tm
3. **✅ Registration**: Registers new account with YOUR referral code
4. **📨 Verification**: Waits for and processes verification email
5. **📊 Tracking**: Updates statistics and continues cycle
6. **🎯 Batching**: Processes in groups of 50 with approval gates

---

## 🎛️ Configuration Options

### Cycle Management
```python
CYCLES_PER_BIG_CYCLE = 50  # Referrals per batch
WAIT_TIME_BETWEEN_CYCLES = 5  # Seconds between attempts
```

### Timeout Settings
```python
EMAIL_TIMEOUT = 30  # Max wait for email generation
CODE_TIMEOUT = 60   # Max wait for verification code
```

---

## 📊 Output Example

```
🤖 SIMPLUS FULLY AUTOMATED REFERRAL BOT
🚀 Starting fully automated referral generation...
📋 Big Cycle = 50 referrals | Approval required after each Big Cycle

==================================================
🔄 STARTING CYCLE 1
==================================================

🔄 Generating new temporary email...
✅ Email extracted: temp123@example.com
✅ Verification code sent to: temp123@example.com
⏳ Waiting for verification code...
✅ Verification code extracted: 123456
✅ Registration completed for: temp123@example.com
✅ CYCLE 1 COMPLETED SUCCESSFULLY!

📊 Statistics: 1/1 successful | Big Cycle 1: 1/50
```

---

## 🔧 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **Mail.tm API Issues** | Check internet connection and retry |
| **Proxy Connection Failed** | Verify proxy credentials and connectivity |
| **Email Generation Failed** | Restart bot, mail.tm may be temporarily down |
| **Timeout Errors** | Check internet connection, increase timeout in settings |
| **Verification Email Not Received** | Wait longer, mail delivery can take 30-60 seconds |
| **Rate Limiting** | Enable proxy rotation or reduce frequency |

### Debug Mode

Enable detailed logging by adding:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📈 Best Practices

### ✅ Recommended
- Monitor success rates and adjust timing
- Take breaks between big cycles  
- Keep API credentials secure
- Test with small batches first
- Respect platform rate limits

### ❌ Avoid
- Running 24/7 without breaks
- Sharing API credentials
- Ignoring error messages
- Excessive rapid requests
- Using on production accounts initially

---

## 🛡️ Security Notes

- **🔐 Never commit API credentials to version control**
- **🗂️ Session files contain login data - keep private**
- **🔄 Rotate credentials periodically**
- **📊 Monitor usage to avoid account restrictions**
- **🚫 Don't share session files**

---

## 📁 Project Structure

```
📂 Simplus_Refer_gen/
├── 📄 app.py               # Flask web application
├── 📄 automated.py         # Core bot logic
├── 📄 config.json          # Runtime configuration
├── 📄 .env                 # Environment variables (local)
├── 📄 .env.example         # Environment template
├── 📄 .gitignore           # Git exclusions
├── 📄 requirements.txt     # Python dependencies
├── 📄 Procfile             # Render deployment config
├── 📄 runtime.txt          # Python version
├── 📄 setup_check.py       # Verification script
├── 📄 README.md            # This documentation
├── 📄 LICENSE              # MIT License
├── 📂 templates/           # HTML templates
│   ├── dashboard.html      # Control panel
│   ├── settings.html       # Configuration page
│   └── login.html          # Authentication
└── 📂 .git/               # Git repository
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **💾 Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **📤 Push** to branch (`git push origin feature/amazing-feature`)
5. **🔄 Open** a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/Simplus_Refer_gen.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
```

---

## 📊 Statistics & Analytics

The bot provides comprehensive tracking:

- **📈 Success Rate**: Percentage of successful referrals
- **⏱️ Timing**: Average time per cycle
- **🔄 Cycles Completed**: Total and current big cycle progress  
- **🎯 Efficiency**: Referrals per hour/day
- **📉 Error Analysis**: Common failure points

---

## 🆘 Support

### Getting Help

1. **📚 Check Documentation**: Read this README thoroughly
2. **� Join Telegram Community**: [t.me/RootLayerR](https://t.me/RootLayerR) - Ask questions and get quick help
3. **🐛 Search Issues**: Look for existing solutions on GitHub
4. **💡 Create Issue**: Provide detailed error information with logs
5. **⭐ Star the Repo**: Support the project at [github.com/devtint/Simplus_Refer_gen](https://github.com/devtint/Simplus_Refer_gen)

### Issue Template
```
**Environment:**
- OS: [Windows/Mac/Linux]
- Python Version: [3.x.x]
- Error Message: [Full error text]

**Steps to Reproduce:**
1. ...
2. ...

**Expected vs Actual Behavior:**
...
```

---

## � Join Our Community

<div align="center">

### 🎯 Connect With Us!

[![Telegram Community](https://img.shields.io/badge/Telegram-Join%20Community-blue?style=for-the-badge&logo=telegram)](https://t.me/RootLayerR)
[![GitHub Stars](https://img.shields.io/github/stars/devtint/Simplus_Refer_gen?style=for-the-badge&logo=github)](https://github.com/devtint/Simplus_Refer_gen)

</div>

**Join our Telegram community for:**

- 💡 **Tips & Tricks**: Learn best practices from experienced users
- 🐛 **Quick Support**: Get help from community members
- 📢 **Updates**: Stay informed about new features and improvements
- 🤝 **Collaboration**: Share your experiences and help others
- 🎉 **Exclusive Content**: Early access to updates and features

**Community Guidelines:**
- ✅ Be respectful and helpful
- ✅ Share knowledge and experiences
- ✅ Report bugs and suggest features
- ❌ No spam or self-promotion
- ❌ No sharing of personal credentials

**Quick Links:**
- 📱 Telegram: [t.me/RootLayerR](https://t.me/RootLayerR)
- ⭐ GitHub: [github.com/devtint/Simplus_Refer_gen](https://github.com/devtint/Simplus_Refer_gen)

---

## �📜 License

This project is licensed under the [MIT License](LICENSE).

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

**Educational Use Disclaimer:** This software is provided for educational purposes. 
Users are responsible for ensuring compliance with platform terms of service and applicable laws.

---

## 🙏 Acknowledgments

- **Mail.tm API** - Reliable temporary email service
- **Flask Framework** - Powerful web framework for dashboard  
- **Selenium WebDriver** - Web automation capabilities
- **Community Contributors** - Bug reports and improvements

---

## 📞 Contact & Links

- **🌟 GitHub**: [@devtint](https://github.com/devtint)
- **📦 Project**: [Simplus_Refer_gen](https://github.com/devtint/Simplus_Refer_gen)
- **💬 Telegram**: [t.me/RootLayerR](https://t.me/RootLayerR)
- **⭐ Star Us**: [GitHub Repository](https://github.com/devtint/Simplus_Refer_gen)

---

<div align="center">

**Made with ❤️ for Educational Purposes**

*Use responsibly and ethically*

[⭐ Star this repo](https://github.com/devtint/Simplus_Refer_gen) • [💬 Join Community](https://t.me/RootLayerR) • [🐛 Report Bug](https://github.com/devtint/Simplus_Refer_gen/issues) • [✨ Request Feature](https://github.com/devtint/Simplus_Refer_gen/issues)

</div>