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

# Your Telegram API credentials (from https://my.telegram.org)
# IMPORTANT: Replace these example values with your actual credentials!
API_ID = '12345678'  # Replace with your actual API ID from my.telegram.org
API_HASH = 'your_api_hash_here'  # Replace with your actual API HASH from my.telegram.org
PHONE_NUMBER = '+1234567890'  # Replace with your actual phone number (with country code)

# Temp mail bot username
# IMPORTANT: Make sure to start @TempMail_org_bot on Telegram before running this script!
# Search for it, click Start, and generate at least one test email to ensure it's working.
TEMP_MAIL_BOT = 'TempMail_org_bot'

class SimplusAutoReferBot:
    def __init__(self):
        self.client = None
        self.current_email = None
        self.verification_code = None
        self.email_received = asyncio.Event()
        self.code_received = asyncio.Event()
        
        # Setup requests session for Simplus API
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
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
            "nation_code": "66",
            "is_register": True
        }
        
        try:
            response = self.session.post(url, json=payload)
            print(f"✅ Verification code sent to: {email}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending verification: {e}")
            return False

    def register_user(self, email, verification_code):
        """Register new user with your referral code to generate a referral for your account"""
        url = "https://m.simplus.online/crmapi/register_user/"
        
        payload = {
            "account_type": "email",
            "account": email,
            "email": email,
            "code": verification_code,
            "nation_code": "66",
            "invitation_code": "TH2511134LYR"  # IMPORTANT: Change this to your actual referral code!
        }
        
        try:
            response = self.session.post(url, json=payload)
            print(f"✅ Registration completed for: {email}")
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

    async def run_cycle(self, cycle_number):
        """Run one complete referral generation cycle"""
        print(f"\n{'='*50}")
        print(f"🔄 STARTING CYCLE {cycle_number}")
        print(f"{'='*50}")
        
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
        success = self.register_user(email, code)
        
        if success:
            print(f"✅ CYCLE {cycle_number} COMPLETED SUCCESSFULLY!")
        else:
            print(f"❌ CYCLE {cycle_number} FAILED!")
        
        return success

    async def send_thank_you_message(self):
        """Send thank you message to BadCodeWriter"""
        try:
            await self.client.send_message('@BadCodeWriter', 'Hi I am using the script and thanks for your help')
            print("✅ Thank you message sent to @BadCodeWriter")
        except Exception as e:
            print(f"⚠️ Could not send thank you message: {e}")

    async def send_completion_message(self, big_cycle_num, cycles_completed, success_count):
        """Send completion message to BadCodeWriter after big cycle"""
        try:
            message = f"I have finished Big Cycle {big_cycle_num} (Completed {cycles_completed} cycles with {success_count} successes). Obtained 1000 coins, Thank you! 🎉"
            await self.client.send_message('@BadCodeWriter', message)
            print("✅ Completion message sent to @BadCodeWriter")
        except Exception as e:
            print(f"⚠️ Could not send completion message: {e}")

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
        print("📋 Big Cycle = 50 referrals | Approval required after each Big Cycle")
        
        # Setup Telegram
        await self.setup_telegram()
        
        # Send thank you message
        await self.send_thank_you_message()
        
        cycle_count = 1
        success_count = 0
        big_cycle_count = 1
        CYCLES_PER_BIG_CYCLE = 50
        
        try:
            while True:
                # Run one cycle
                success = await self.run_cycle(cycle_count)
                if success:
                    success_count += 1
                
                cycles_in_current_big_cycle = ((cycle_count - 1) % CYCLES_PER_BIG_CYCLE) + 1
                print(f"\n📊 Statistics: {success_count}/{cycle_count} successful | Big Cycle {big_cycle_count}: {cycles_in_current_big_cycle}/{CYCLES_PER_BIG_CYCLE}")
                
                # Check if big cycle is complete
                if cycle_count % CYCLES_PER_BIG_CYCLE == 0:
                    print(f"\n🎉 BIG CYCLE {big_cycle_count} COMPLETED!")
                    print(f"📊 Results: {success_count}/{cycle_count} total successful referrals generated")
                    
                    # Send completion message to BadCodeWriter
                    await self.send_completion_message(big_cycle_count, CYCLES_PER_BIG_CYCLE, success_count)
                    
                    # Ask for approval to continue
                    if not self.get_user_approval():
                        print("\n🛑 Bot stopped by user choice")
                        break
                    
                    big_cycle_count += 1
                    print(f"\n🚀 Starting Big Cycle {big_cycle_count}...")
                
                cycle_count += 1
                
                # Wait before next cycle (only if not at end of big cycle)
                if cycle_count % CYCLES_PER_BIG_CYCLE != 1:
                    print("⏳ Waiting 5 seconds before next cycle...")
                    await asyncio.sleep(5)
                
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