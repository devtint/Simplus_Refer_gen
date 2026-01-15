"""
Simplus Auto Referral Bot

This bot automatically generates referrals for your Simplus account using temporary emails.
Each successful registration counts as a referral to your account, helping you earn rewards.

For Educational Purposes Only

BEFORE RUNNING:
1. Get your Telegram API credentials from https://my.telegram.org (Still needed for legacy compatibility)
2. Replace API_ID, API_HASH, and PHONE_NUMBER with your actual values
3. Change the invitation_code to YOUR referral code (this is how you get referrals)
4. Install required packages: pip install requests python-dotenv
5. NEW: Now uses mail.tm API for temporary emails - No Telegram bot required!

FEATURES:
- Direct mail.tm API integration (faster and more reliable)
- Proxy rotation support for better anonymization
- User-Agent rotation to avoid detection
- Automatic failed proxy blacklisting

DISCLAIMER: This script is for educational purposes only.
Use responsibly and in accordance with platform terms of service.
"""

import asyncio
import re
import requests
from telethon import TelegramClient, events
import time
import os
import random
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your Telegram API credentials (from .env file)
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

# Validate required credentials
if not all([API_ID, API_HASH, PHONE_NUMBER]):
    raise ValueError("Missing required Telegram credentials in .env file")

# Load invitation codes (supports multiple codes separated by comma)
INVITATION_CODES = [code.strip() for code in os.getenv('INVITATION_CODES', '').split(',') if code.strip()]

# Mail.tm API configuration
MAILTM_BASE_URL = 'https://api.mail.tm'

# List of realistic User-Agent strings to rotate and avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
]

class SimplusAutoReferBot:
    def __init__(self, proxy_list=None, use_proxy=False):
        self.client = None
        self.current_email = None
        self.verification_code = None
        self.email_received = asyncio.Event()
        self.code_received = asyncio.Event()
        
        # Mail.tm API configuration
        self.mail_account = None
        self.mail_token = None
        self.mail_password = None
        
        # Proxy configuration
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list if proxy_list else []
        self.failed_proxies = set()  # Track failed proxies
        self.current_proxy = None
        
        # Setup requests session for Simplus API with random User-Agent
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/json;charset=UTF-8;",
            "Language": "th",
            "X-Crm-Country": "th",
            "Origin": "https://m.simplus.online",
            "Cookie": "hello"
        })
        
        # Set proxy if enabled
        if self.use_proxy and self.proxy_list:
            self._rotate_proxy()
    
    def _rotate_proxy(self):
        """Select a random working proxy from the list"""
        available_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available_proxies:
            print("⚠️ All proxies have failed! Resetting failed proxy list...")
            self.failed_proxies.clear()
            available_proxies = self.proxy_list.copy()
        
        if available_proxies:
            self.current_proxy = random.choice(available_proxies)
            self.session.proxies = {
                'http': self.current_proxy,
                'https': self.current_proxy
            }
            print(f"🌐 Using proxy: {self.current_proxy.split('@')[1] if '@' in self.current_proxy else self.current_proxy}")
        else:
            print("⚠️ No proxies available, running without proxy")
            self.session.proxies = {}
            self.current_proxy = None
    
    def _mark_proxy_failed(self):
        """Mark current proxy as failed and rotate to a new one"""
        if self.current_proxy:
            self.failed_proxies.add(self.current_proxy)
            print(f"❌ Proxy failed and blacklisted: {self.current_proxy.split('@')[1] if '@' in self.current_proxy else self.current_proxy}")
            print(f"📊 Failed proxies: {len(self.failed_proxies)}/{len(self.proxy_list)}")
            self._rotate_proxy()

    def get_mail_domains(self):
        """Get available domains from mail.tm"""
        try:
            response = self.session.get(f"{MAILTM_BASE_URL}/domains", timeout=15)
            if response.status_code == 200:
                data = response.json()
                domains = [domain['domain'] for domain in data['hydra:member'] if domain.get('isActive', True)]
                return domains
            else:
                print(f"❌ Failed to get domains: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting domains: {e}")
            if self.use_proxy and self.current_proxy:
                self._mark_proxy_failed()
                return self.get_mail_domains()  # Retry with new proxy
            return []

    def create_mail_account(self):
        """Create a new temporary email account"""
        try:
            domains = self.get_mail_domains()
            if not domains:
                print("❌ No available domains")
                return None
            
            # Generate random username and use first available domain
            username = f"user{random.randint(100000, 999999)}"
            domain = random.choice(domains)
            email = f"{username}@{domain}"
            password = f"pass{random.randint(100000, 999999)}"
            
            # Create account
            payload = {
                "address": email,
                "password": password
            }
            
            response = self.session.post(f"{MAILTM_BASE_URL}/accounts", json=payload, timeout=15)
            
            if response.status_code == 201:
                account_data = response.json()
                self.mail_account = account_data
                self.mail_password = password
                self.current_email = email
                
                # Get authentication token
                token_response = self.session.post(f"{MAILTM_BASE_URL}/token", json={
                    "address": email,
                    "password": password
                }, timeout=15)
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    self.mail_token = token_data['token']
                    print(f"✅ Created email account: {email}")
                    return email
                else:
                    print(f"❌ Failed to get token: {token_response.status_code}")
                    return None
            else:
                print(f"❌ Failed to create account: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating mail account: {e}")
            if self.use_proxy and self.current_proxy:
                self._mark_proxy_failed()
                return self.create_mail_account()  # Retry with new proxy
            return None

    def get_verification_code_from_email(self, max_attempts=12, delay=5):
        """Get verification code from the latest email"""
        if not self.mail_token:
            print("❌ No mail token available")
            return None
            
        headers = {"Authorization": f"Bearer {self.mail_token}"}
        
        for attempt in range(max_attempts):
            try:
                print(f"📨 Checking for emails... (Attempt {attempt + 1}/{max_attempts})")
                
                # Get messages
                response = self.session.get(f"{MAILTM_BASE_URL}/messages", headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('hydra:member', [])
                    
                    if messages:
                        # Get the latest message
                        latest_message = messages[0]
                        message_id = latest_message['id']
                        
                        # Get full message content
                        msg_response = self.session.get(f"{MAILTM_BASE_URL}/messages/{message_id}", headers=headers, timeout=15)
                        
                        if msg_response.status_code == 200:
                            message_data = msg_response.json()
                            
                            # Try to extract verification code from text and html
                            text_content = message_data.get('text', '')
                            html_content = ' '.join(message_data.get('html', []))
                            full_content = text_content + ' ' + html_content
                            
                            # Look for 6-digit verification code
                            code_patterns = [
                                r'(\d{6})\s+is your verification code',
                                r'verification code:\s*(\d{6})',
                                r'code:\s*(\d{6})',
                                r'OTP:\s*(\d{6})',
                                r'\b(\d{6})\b'
                            ]
                            
                            for pattern in code_patterns:
                                match = re.search(pattern, full_content, re.IGNORECASE)
                                if match:
                                    code = match.group(1)
                                    print(f"✅ Verification code found: {code}")
                                    return code
                            
                            print("⚠️ Email received but no verification code found")
                            print(f"📄 Email content preview: {full_content[:200]}...")
                    
                    else:
                        print("📭 No messages yet, waiting...")
                
                elif response.status_code == 401:
                    print("❌ Authentication failed, token might be expired")
                    return None
                else:
                    print(f"❌ Failed to get messages: {response.status_code}")
                
            except Exception as e:
                print(f"❌ Error checking emails: {e}")
                if self.use_proxy and self.current_proxy:
                    self._mark_proxy_failed()
            
            if attempt < max_attempts - 1:
                time.sleep(delay)
        
        print("❌ Timeout waiting for verification code")
        return None

    async def setup_telegram(self):
        """Setup Telegram client - DEPRECATED: Now using mail.tm API"""
        print("📱 Telegram setup skipped - Using mail.tm API instead")
        print("✅ Mail.tm API ready for email generation")

    def send_verification_code(self, email):
        """Send verification code to email via Simplus API"""
        url = "https://m.simplus.online/crmapi/send_verification_code/"
        
        payload = {
            "account": email,
            "account_type": "email",
            "nation_code": os.getenv('NATION_CODE'),
            "is_register": True
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=15)
            print(f"✅ Verification code sent to: {email}")
            return response.status_code == 200
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            print(f"❌ Proxy/Connection error sending verification: {e}")
            if self.use_proxy and self.current_proxy:
                self._mark_proxy_failed()
            return False
        except Exception as e:
            print(f"❌ Error sending verification: {e}")
            return False

    def register_user(self, email, verification_code, invitation_code):
        """Register new user with your referral code to generate a referral for your account"""
        url = "https://m.simplus.online/crmapi/register_user/"
        
        payload = {
            "account_type": "email",
            "account": email,
            "email": email,
            "code": verification_code,
            "nation_code": os.getenv('NATION_CODE'),
            "invitation_code": invitation_code
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=15)
            print(f"✅ Registration completed for: {email} with code: {invitation_code}")
            return response.status_code == 200
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            print(f"❌ Proxy/Connection error during registration: {e}")
            if self.use_proxy and self.current_proxy:
                self._mark_proxy_failed()
            return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    async def generate_new_email(self):
        """Generate a new temporary email using mail.tm API"""
        print("\n🔄 Generating new temporary email via mail.tm...")
        email = self.create_mail_account()
        if email:
            print(f"✅ Email generated: {email}")
            return email
        else:
            print("❌ Failed to generate email")
            return None

    async def wait_for_verification_code(self):
        """Wait for verification code from mail.tm"""
        print("⏳ Waiting for verification code via mail.tm...")
        code = self.get_verification_code_from_email()
        if code:
            print(f"✅ Verification code received: {code}")
            return code
        else:
            print("❌ Failed to get verification code")
            return None

    async def run_cycle(self, loop_count, code_index, total_codes, invitation_code):
        """Run one complete referral generation cycle"""
        print(f"\n{'='*60}")
        print(f"🔄 LOOP {loop_count} | Processing Code {code_index}/{total_codes}: {invitation_code}")
        print(f"{'='*60}")
        
        # Rotate User-Agent for each cycle to avoid detection
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
        
        # Rotate proxy for each cycle if enabled
        if self.use_proxy and self.proxy_list:
            self._rotate_proxy()
        
        # Step 1: Generate new email
        email = await self.generate_new_email()
        if not email:
            return False
        
        # Step 2: Send verification code
        if not self.send_verification_code(email):
            return False
        
        # Step 3: Wait for verification code
        code = await self.wait_for_verification_code()
        if not code:
            return False
        
        # Step 4: Register user
        success = self.register_user(email, code, invitation_code)
        
        if success:
            print(f"✅ LOOP {loop_count} - Code {code_index}/{total_codes} COMPLETED SUCCESSFULLY!")
        else:
            print(f"❌ LOOP {loop_count} - Code {code_index}/{total_codes} FAILED!")
        
        return success

    # Removed: No longer sending thank you messages

    # Removed: No longer sending completion messages

    def get_user_approval(self):
        """Get user approval to continue with next big cycle"""
        while True:
            response = input("\n❓ Continue with next Big Cycle? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")

    async def run_continuous(self):
        """Run continuous referral generation cycles with big cycle management"""
        print("🤖 SIMPLUS FULLY AUTOMATED REFERRAL BOT")
        print("🚀 Starting fully automated referral generation...")
        print("📧 Using mail.tm API for temporary emails (No Telegram required!)")
        print(f"📋 Big Cycle = 50 loops | {len(INVITATION_CODES)} codes per loop | Approval required after each Big Cycle")
        print(f"📝 Loaded {len(INVITATION_CODES)} invitation codes: {', '.join(INVITATION_CODES)}")
        
        if not INVITATION_CODES:
            print("❌ ERROR: No invitation codes found in .env file!")
            return
        
        # Setup (no more Telegram needed)
        await self.setup_telegram()
        
        loop_count = 1
        total_success_count = 0
        big_cycle_count = 1
        LOOPS_PER_BIG_CYCLE = 50
        
        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🔄 STARTING LOOP {loop_count} - Processing {len(INVITATION_CODES)} referral codes")
                print(f"{'='*60}")
                
                loop_success_count = 0
                
                # Process each invitation code in this loop
                for idx, invitation_code in enumerate(INVITATION_CODES, 1):
                    success = await self.run_cycle(loop_count, idx, len(INVITATION_CODES), invitation_code)
                    if success:
                        loop_success_count += 1
                        total_success_count += 1
                    
                    # Wait 10 seconds between each code (except after the last one)
                    if idx < len(INVITATION_CODES):
                        print("⏳ Waiting 10 seconds before next code...")
                        await asyncio.sleep(10)
                
                print(f"\n✅ Loop {loop_count} completed: {loop_success_count}/{len(INVITATION_CODES)} successful")
                
                loops_in_current_big_cycle = ((loop_count - 1) % LOOPS_PER_BIG_CYCLE) + 1
                print(f"📊 Overall Statistics: {total_success_count} total successful | Big Cycle {big_cycle_count}: {loops_in_current_big_cycle}/{LOOPS_PER_BIG_CYCLE} loops")
                
                # Check if big cycle is complete
                if loop_count % LOOPS_PER_BIG_CYCLE == 0:
                    print(f"\n🎉 BIG CYCLE {big_cycle_count} COMPLETED!")
                    print(f"📊 Results: {total_success_count} total successful referrals generated")
                    
                    # Ask for approval to continue
                    if not self.get_user_approval():
                        print("\n🛑 Bot stopped by user choice")
                        break
                    
                    big_cycle_count += 1
                    print(f"\n🚀 Starting Big Cycle {big_cycle_count}...")
                
                loop_count += 1
                
                # Wait 6000 seconds after completing all codes (only if not at end of big cycle)
                if loop_count % LOOPS_PER_BIG_CYCLE != 1:
                    print("⏳ Waiting 6000 seconds before next loop...")
                    #recommend very long interval to avoid detect
                    await asyncio.sleep(6000)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            print("✅ Bot session ended")

async def main():
    print("🚀 Starting Simplus Auto Referral Generator Bot...")
    print("📧 Now using mail.tm API - No Telegram setup required!")
    print(f"Made with ❤️ by TYRELL (Only for educational purposes, NO illegal use!)")
    automator = SimplusAutoReferBot()
    await automator.run_continuous()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())