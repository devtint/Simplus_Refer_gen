"""
Simplus Auto Referral Bot

This bot automatically generates referrals for your Simplus account using temporary emails.
Each successful registration counts as a referral to your account, helping you earn rewards.

For Educational Purposes Only

BEFORE RUNNING:
1. Get your Telegram API credentials from https://my.telegram.org
2. Replace API_ID, API_HASH, and PHONE_NUMBER with your actual values
3. Change the invitation_code to YOUR referral code (this is how you get referrals)
4. Install required packages: pip install telethon requests
5. IMPORTANT: Start @TempMail_org_bot on Telegram first and generate at least one email
   - Search for @TempMail_org_bot in Telegram
   - Start the bot with /start command
   - Generate a test email to ensure it's working

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

# Temp mail bot username
# IMPORTANT: Make sure to start @TempMail_org_bot on Telegram before running this script!
# Search for it, click Start, and generate at least one test email to ensure it's working.
TEMP_MAIL_BOT = 'TempMail_org_bot'

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
    def __init__(self):
        self.client = None
        self.current_email = None
        self.verification_code = None
        self.email_received = asyncio.Event()
        self.code_received = asyncio.Event()
        
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

    async def setup_telegram(self):
        """Setup Telegram client with event handlers"""
        print("📱 Setting up Telegram client...")
        print("⚠️  REMINDER: Make sure @TempMail_org_bot is started and working!")
        
        self.client = TelegramClient('session', API_ID, API_HASH)
        
        @self.client.on(events.NewMessage(from_users=TEMP_MAIL_BOT))
        async def handler(event):
            message = event.message.text
            print(f"\n📨 Bot Message: {message}")
            
            # Extract temporary email from message (only when it's actually generated)
            if any(keyword in message.lower() for keyword in ['temporary email', 'new email', 'generated']):
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
                if email_match:
                    self.current_email = email_match.group()
                    print(f"✅ Email extracted: {self.current_email}")
                    self.email_received.set()
            
            # Extract verification code from OTP messages
            code_match = re.search(r'(\d{6})\s+is your verification code', message)
            if code_match:
                self.verification_code = code_match.group(1)
                print(f"✅ Verification code extracted: {self.verification_code}")
                self.code_received.set()
            else:
                # Alternative pattern for verification codes
                code_match = re.search(r'\b(\d{6})\b', message)
                if code_match and 'verification' in message.lower():
                    self.verification_code = code_match.group(1)
                    print(f"✅ Verification code extracted: {self.verification_code}")
                    self.code_received.set()

        # Start the client
        await self.client.start(PHONE_NUMBER)
        print("✅ Telegram client started successfully")
        
        # Ensure we're connected to the temp mail bot
        print("✅ Connected to temp mail bot")

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
            response = self.session.post(url, json=payload)
            print(f"✅ Verification code sent to: {email}")
            return response.status_code == 200
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
            response = self.session.post(url, json=payload)
            print(f"✅ Registration completed for: {email} with code: {invitation_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    async def generate_new_email(self):
        """Generate a new temporary email"""
        print("\n🔄 Generating new temporary email...")
        await self.client.send_message(TEMP_MAIL_BOT, '➕ Generate New / Delete')
        self.email_received.clear()
        
        # Wait for email (max 30 seconds)
        try:
            await asyncio.wait_for(self.email_received.wait(), timeout=30.0)
            return self.current_email
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for email generation")
            return None

    async def wait_for_verification_code(self):
        """Wait for verification code from bot"""
        print("⏳ Waiting for verification code...")
        self.code_received.clear()
        
        # Wait for verification code (max 60 seconds)
        try:
            await asyncio.wait_for(self.code_received.wait(), timeout=60.0)
            return self.verification_code
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for verification code")
            return None

    async def run_cycle(self, loop_count, code_index, total_codes, invitation_code):
        """Run one complete referral generation cycle"""
        print(f"\n{'='*60}")
        print(f"🔄 LOOP {loop_count} | Processing Code {code_index}/{total_codes}: {invitation_code}")
        print(f"{'='*60}")
        
        # Rotate User-Agent for each cycle to avoid detection
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})
        
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
        print(f"📋 Big Cycle = 50 loops | {len(INVITATION_CODES)} codes per loop | Approval required after each Big Cycle")
        print(f"📝 Loaded {len(INVITATION_CODES)} invitation codes: {', '.join(INVITATION_CODES)}")
        
        if not INVITATION_CODES:
            print("❌ ERROR: No invitation codes found in .env file!")
            return
        
        # Setup Telegram
        await self.setup_telegram()
        
        # Send thank you message
        await self.send_thank_you_message()
        
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
                    
                    # Send completion message to BadCodeWriter
                    await self.send_completion_message(big_cycle_count, LOOPS_PER_BIG_CYCLE, total_success_count)
                    
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
            await self.client.disconnect()
            print("✅ Telegram client disconnected")

async def main():
    print("🚀 Starting Simplus Auto Referral Generator Bot...")
    print(f"Made with ❤️ by TYRELL (Only for educational purposes, NO illegal use!)")
    automator = SimplusAutoReferBot()
    await automator.run_continuous()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())