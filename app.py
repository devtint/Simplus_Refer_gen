"""
Flask Web UI for Simplus Auto Referral Bot
Control panel for managing and monitoring the bot
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import asyncio
import threading
import os
import json
import requests
from datetime import datetime, timedelta
from automated import SimplusAutoReferBot

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'simplus-secret-key-change-this')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Config file path
CONFIG_FILE = 'config.json'

# Load config
def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        # Initialize from env if config doesn't exist
        proxy_list_str = os.getenv('PROXY_LIST', '')
        proxy_list = [p.strip() for p in proxy_list_str.split(',') if p.strip()] if proxy_list_str else []
        
        config = {
            'invitation_codes': [code.strip() for code in os.getenv('INVITATION_CODES', '').split(',') if code.strip()],
            'wait_between_codes': 10,
            'wait_between_loops': 6000,
            'loops_per_big_cycle': 50,
            'use_proxy': False,
            'proxy_list': proxy_list
        }
        save_config(config)
    
    # Ensure proxy settings exist in config
    if 'use_proxy' not in config:
        config['use_proxy'] = False
    if 'proxy_list' not in config:
        config['proxy_list'] = []
    
    return config

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Bot state management
bot_state = {
    'running': False,
    'paused': False,
    'current_loop': 0,
    'total_success': 0,
    'total_attempts': 0,
    'current_big_cycle': 1,
    'loops_in_cycle': 0,
    'last_activity': None,
    'logs': [],
    'keep_alive_status': {
        'last_ping': None,
        'status': 'inactive',
        'next_ping': None
    }
}

bot_instance = None
bot_thread = None
keep_alive_thread = None

# Simple user class for authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def add_log(message, level='info'):
    """Add log message to state"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bot_state['logs'].append({
        'timestamp': timestamp,
        'message': message,
        'level': level
    })
    # Keep only last 30 logs
    if len(bot_state['logs']) > 30:
        bot_state['logs'] = bot_state['logs'][-30:]
    bot_state['last_activity'] = timestamp

def keep_alive_ping():
    """Ping the app every 5 minutes to keep it alive"""
    keep_alive_url = os.getenv('KEEP_ALIVE_URL', '')
    
    if not keep_alive_url or keep_alive_url in ['https://your-app-name.onrender.com', 'http://127.0.0.1:5000/', 'http://localhost:5000']:
        add_log("Keep-alive URL not configured or using localhost. Skipping keep-alive pings.", "warning")
        bot_state['keep_alive_status']['status'] = 'disabled'
        return
    
    while True:
        try:
            bot_state['keep_alive_status']['status'] = 'active'
            response = requests.get(f"{keep_alive_url.rstrip('/')}/ping", timeout=10)
            now = datetime.now()
            bot_state['keep_alive_status']['last_ping'] = now.strftime('%Y-%m-%d %H:%M:%S')
            bot_state['keep_alive_status']['next_ping'] = (now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            
            if response.status_code == 200:
                add_log(f"Keep-alive ping successful", "success")
            else:
                add_log(f"Keep-alive ping returned status {response.status_code}", "warning")
        except requests.exceptions.Timeout:
            add_log(f"Keep-alive ping timeout", "error")
        except requests.exceptions.ConnectionError:
            add_log(f"Keep-alive connection failed. Check if URL is correct.", "error")
        except Exception as e:
            add_log(f"Keep-alive error: {str(e)}", "error")
        
        # Wait 5 minutes before next ping
        threading.Event().wait(300)

async def run_bot():
    """Run the bot asynchronously"""
    global bot_instance
    
    config = load_config()
    invitation_codes = config['invitation_codes']
    
    if not invitation_codes:
        add_log("No invitation codes configured!", "error")
        bot_state['running'] = False
        return
    
    # Initialize bot with proxy configuration
    use_proxy = config.get('use_proxy', False)
    proxy_list = config.get('proxy_list', [])
    
    bot_instance = SimplusAutoReferBot(
        proxy_list=proxy_list if use_proxy else None,
        use_proxy=use_proxy
    )
    
    add_log("Bot initialized successfully", "success")
    add_log(f"Loaded {len(invitation_codes)} invitation codes", "info")
    if use_proxy and proxy_list:
        add_log(f"Proxy enabled with {len(proxy_list)} proxies", "success")
    else:
        add_log("Proxy disabled", "info")
    
    try:
        # Setup Telegram
        await bot_instance.setup_telegram()
        add_log("Connected to Telegram", "success")
        
        loop_count = 1
        total_success_count = 0
        big_cycle_count = 1
        
        while bot_state['running']:
            if bot_state['paused']:
                await asyncio.sleep(1)
                continue
            
            # Reload config for each loop
            config = load_config()
            invitation_codes = config['invitation_codes']
            wait_between_codes = config['wait_between_codes']
            wait_between_loops = config['wait_between_loops']
            loops_per_big_cycle = config['loops_per_big_cycle']
            
            bot_state['current_loop'] = loop_count
            bot_state['current_big_cycle'] = big_cycle_count
            bot_state['loops_in_cycle'] = ((loop_count - 1) % loops_per_big_cycle) + 1
            
            add_log(f"Starting Loop {loop_count} - Processing {len(invitation_codes)} codes", "info")
            
            loop_success_count = 0
            
            # Process each invitation code
            for idx, invitation_code in enumerate(invitation_codes, 1):
                if not bot_state['running'] or bot_state['paused']:
                    break
                
                add_log(f"Processing code {idx}/{len(invitation_codes)}: {invitation_code}", "info")
                
                success = await bot_instance.run_cycle(loop_count, idx, len(invitation_codes), invitation_code)
                bot_state['total_attempts'] += 1
                
                if success:
                    loop_success_count += 1
                    total_success_count += 1
                    bot_state['total_success'] = total_success_count
                    add_log(f"Code {idx}/{len(invitation_codes)} successful!", "success")
                else:
                    add_log(f"Code {idx}/{len(invitation_codes)} failed", "error")
                
                # Wait between codes
                if idx < len(invitation_codes) and bot_state['running']:
                    await asyncio.sleep(wait_between_codes)
            
            add_log(f"Loop {loop_count} completed: {loop_success_count}/{len(invitation_codes)} successful", "success")
            
            # Check if big cycle is complete
            if loop_count % loops_per_big_cycle == 0:
                add_log(f"BIG CYCLE {big_cycle_count} COMPLETED! Total: {total_success_count} successful", "success")
                big_cycle_count += 1
            
            loop_count += 1
            
            # Wait between loops
            if bot_state['running'] and loop_count % loops_per_big_cycle != 1:
                add_log(f"Waiting {wait_between_loops} seconds before next loop...", "info")
                for _ in range(wait_between_loops):
                    if not bot_state['running'] or bot_state['paused']:
                        break
                    await asyncio.sleep(1)
        
        add_log("Bot stopped by user", "warning")
        
    except Exception as e:
        add_log(f"Bot error: {str(e)}", "error")
    finally:
        if bot_instance and bot_instance.client:
            await bot_instance.client.disconnect()
        bot_state['running'] = False
        add_log("Bot disconnected", "info")

def run_bot_thread():
    """Run bot in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == os.getenv('WEB_USERNAME', 'admin') and password == os.getenv('WEB_PASSWORD', 'simplus2026'):
            user = User(username)
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/status')
@login_required
def get_status():
    """Get current bot status"""
    config = load_config()
    return jsonify({
        **bot_state,
        'codes_count': len(config['invitation_codes'])
    })

@app.route('/api/start', methods=['POST'])
@login_required
def start_bot():
    """Start the bot"""
    global bot_thread
    
    if bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is already running'})
    
    config = load_config()
    if not config['invitation_codes']:
        return jsonify({'success': False, 'message': 'No invitation codes configured'})
    
    bot_state['running'] = True
    bot_state['paused'] = False
    bot_state['current_loop'] = 0
    bot_state['total_success'] = 0
    bot_state['total_attempts'] = 0
    
    add_log("Starting bot...", "info")
    
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    return jsonify({'success': True, 'message': 'Bot started successfully'})

@app.route('/api/stop', methods=['POST'])
@login_required
def stop_bot():
    """Stop the bot"""
    if not bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is not running'})
    
    bot_state['running'] = False
    bot_state['paused'] = False
    add_log("Stopping bot...", "warning")
    
    return jsonify({'success': True, 'message': 'Bot stopped'})

@app.route('/api/pause', methods=['POST'])
@login_required
def pause_bot():
    """Pause the bot"""
    if not bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is not running'})
    
    bot_state['paused'] = not bot_state['paused']
    status = 'paused' if bot_state['paused'] else 'resumed'
    add_log(f"Bot {status}", "warning")
    
    return jsonify({'success': True, 'message': f'Bot {status}', 'paused': bot_state['paused']})

@app.route('/api/logs')
@login_required
def get_logs():
    """Get recent logs"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({'logs': bot_state['logs'][-limit:]})

@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """Get configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    """Update configuration"""
    try:
        data = request.json
        config = load_config()
        
        # Update invitation codes
        if 'invitation_codes' in data:
            codes = data['invitation_codes']
            if isinstance(codes, str):
                codes = [c.strip() for c in codes.split(',') if c.strip()]
            config['invitation_codes'] = codes
        
        # Update timings
        if 'wait_between_codes' in data:
            config['wait_between_codes'] = int(data['wait_between_codes'])
        if 'wait_between_loops' in data:
            config['wait_between_loops'] = int(data['wait_between_loops'])
        if 'loops_per_big_cycle' in data:
            config['loops_per_big_cycle'] = int(data['loops_per_big_cycle'])
        
        # Update proxy settings
        if 'use_proxy' in data:
            config['use_proxy'] = bool(data['use_proxy'])
        if 'proxy_list' in data:
            proxies = data['proxy_list']
            if isinstance(proxies, str):
                proxies = [p.strip() for p in proxies.split(',') if p.strip()]
            config['proxy_list'] = proxies
        
        save_config(config)
        add_log("Configuration updated", "success")
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/ping')
def ping():
    """Keep-alive endpoint"""
    return jsonify({'status': 'alive', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
