# Telegram Bot Authentication

Complete guide for authenticating Telegram bots with the backend system.

---

## Table of Contents

1. [Overview](#overview)
2. [Service Token System](#service-token-system)
3. [Authentication Flow](#authentication-flow)
4. [API Endpoints](#api-endpoints)
5. [Bot Implementation](#bot-implementation)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Telegram bots require **long-lived, non-expiring service tokens** to maintain continuous operation without requiring repeated authentication.

### Key Features

- **One-time authentication** via OTP
- **Permanent service tokens** (no expiry)
- **No session management** (bypasses single-session control)
- **Automatic admin status checking**
- **Separate from interactive logins**

### Use Cases

1. **Admin Activity Monitoring Bot**
2. **Device Notification Bot**
3. **SMS Alert Bot**
4. **Command Execution Bot**
5. **Status Monitoring Bot**

---

## Service Token System

### What is a Service Token?

A **service token** is a permanent JWT token that:
- Has no expiration date
- Bypasses single-session control
- Only invalidated if admin is disabled
- Used by background services (bots)

### Service vs Interactive Tokens

| Feature | Interactive Token | Service Token |
|---------|------------------|---------------|
| **Used By** | Web/Mobile admins | Telegram bots |
| **Expiry** | 24 hours | Never |
| **Session Check** | Yes | No |
| **Multi-use** | One active session | Unlimited |
| **Login Method** | Username + Password + OTP | Username + Bot OTP |
| **Revocation** | Logout or new login | Admin disabled only |

### Token Structure

**Service Token JWT:**
```json
{
  "sub": "bot_admin",              // Admin username
  "client_type": "service",        // Token type
  "device_token": "abc123...",     // Admin's device token
  "iat": 1698825600                // Issued at
  // No "exp" field = permanent
  // No "session_id" = bypass session check
}
```

**Interactive Token (for comparison):**
```json
{
  "sub": "admin",
  "client_type": "interactive",
  "session_id": "uuid",
  "exp": 1698912000  // 24h expiry
}
```

---

## Authentication Flow

### Complete Flow Diagram

```
???????????????????????????????????????????????????????????????
?                  Bot Authentication Flow                     ?
???????????????????????????????????????????????????????????????

1. Bot ? POST /bot/auth/request-otp
   Body: { username: "admin" }
   
2. Server validates admin account
   
3. Server generates 6-digit OTP
   
4. Server sends OTP to admin's Telegram (Bot 4)
   
5. Server returns success message
   
6. Admin receives OTP in Telegram
   
7. Bot ? POST /bot/auth/verify-otp
   Body: { username: "admin", otp_code: "123456" }
   
8. Server validates OTP
   
9. Server creates SERVICE TOKEN (permanent)
   
10. Server returns service_token
   
11. Bot saves service_token (use forever)
   
12. Bot periodically checks admin status:
    Bot ? GET /bot/auth/check?username=admin&service_token=TOKEN
    
13. If admin active ? continue working
    If admin disabled ? stop bot
```

### Step-by-Step Process

#### Step 1: Request OTP

```bash
curl -X POST "http://localhost:8000/bot/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"}'
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent to your Telegram (Bot 4). Please verify using /bot/auth/verify-otp"
}
```

**Telegram Message (Bot 4):**
```
?? Bot Authentication

?? Username: admin
?? OTP Code: 749675
? Valid for: 5 minutes

This OTP is for bot authentication.
```

#### Step 2: Verify OTP

```bash
curl -X POST "http://localhost:8000/bot/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "otp_code": "749675"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Bot authenticated successfully",
  "service_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImNsaWVudF90eXBlIjoic2VydmljZSIsImRldmljZV90b2tlbiI6ImFiYzEyMy4uLiIsImlhdCI6MTY5ODgyNTYwMH0.signature",
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "device_token": "abc123...",
    "is_active": true
  }
}
```

**?? IMPORTANT:** Save this `service_token` securely. You won't get it again!

#### Step 3: Periodic Status Check

```bash
curl -X GET "http://localhost:8000/bot/auth/check?username=admin&service_token=YOUR_SERVICE_TOKEN"
```

**Response (Active Admin):**
```json
{
  "is_active": true,
  "username": "admin",
  "device_token": "abc123...",
  "message": "Admin is active"
}
```

**Response (Disabled Admin):**
```json
{
  "is_active": false,
  "username": "admin",
  "device_token": "abc123...",
  "message": "Admin account is disabled"
}
```

---

## API Endpoints

### POST /bot/auth/request-otp
**Request OTP for Bot Authentication**

**Description:** Request OTP code for bot authentication (Step 1).

**Authorization:** None

**Request Body:**
```json
{
  "username": "admin"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP sent to your Telegram (Bot 4). Please verify using /bot/auth/verify-otp"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Admin account is disabled"
}
```

**Features:**
- Validates admin exists
- Checks admin is active
- Generates 6-digit OTP
- Sends via Telegram Bot 4
- OTP expires in 5 minutes

---

### POST /bot/auth/verify-otp
**Verify OTP and Get Service Token**

**Description:** Verify OTP and receive permanent service token (Step 2).

**Authorization:** None

**Request Body:**
```json
{
  "username": "admin",
  "otp_code": "749675"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Bot authenticated successfully",
  "service_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "device_token": "abc123...",
    "is_active": true
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired OTP"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found"
}
```

**Features:**
- Validates OTP code
- Creates permanent service token
- Returns admin details
- Logs bot authentication
- Sends Telegram notification

**Token Details:**
- **Type:** Service token
- **Expiry:** Never
- **Session:** Bypass
- **Use:** Unlimited

---

### GET /bot/auth/check
**Check Admin Status**

**Description:** Verify if admin account is still active.

**Authorization:** Service token via query parameter

**Query Parameters:**
- `username` (string, required): Admin username
- `service_token` (string, required): Service token from Step 2

**Request:**
```bash
GET /bot/auth/check?username=admin&service_token=YOUR_TOKEN
```

**Response (200 OK - Active):**
```json
{
  "is_active": true,
  "username": "admin",
  "device_token": "abc123...",
  "message": "Admin is active"
}
```

**Response (200 OK - Disabled):**
```json
{
  "is_active": false,
  "username": "admin",
  "device_token": "abc123...",
  "message": "Admin account is disabled"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid service token"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found"
}
```

**Features:**
- Validates service token
- Returns admin status
- No expiry check (service tokens permanent)
- No session check (bypasses single-session)

**Use Cases:**
- Bot health checks (every 5 minutes)
- Before sending messages
- After long idle periods
- Startup validation

---

## Bot Implementation

### Python Bot Example

**Complete Bot Implementation:**

```python
import requests
import time
import json
import os

class TelegramBotAuth:
    def __init__(self, base_url, username, token_file="bot_token.json"):
        self.base_url = base_url
        self.username = username
        self.token_file = token_file
        self.service_token = None
        self.device_token = None
        
    def load_token(self):
        """Load saved service token from file"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                self.service_token = data.get('service_token')
                self.device_token = data.get('device_token')
                print("? Token loaded from file")
                return True
        return False
    
    def save_token(self):
        """Save service token to file"""
        with open(self.token_file, 'w') as f:
            json.dump({
                'service_token': self.service_token,
                'device_token': self.device_token,
                'username': self.username
            }, f)
        print("? Token saved to file")
    
    def request_otp(self):
        """Step 1: Request OTP"""
        response = requests.post(
            f"{self.base_url}/bot/auth/request-otp",
            json={"username": self.username}
        )
        
        if response.status_code == 200:
            print("? OTP sent to Telegram")
            return True
        else:
            print(f"? Failed to request OTP: {response.json()}")
            return False
    
    def verify_otp(self, otp_code):
        """Step 2: Verify OTP and get service token"""
        response = requests.post(
            f"{self.base_url}/bot/auth/verify-otp",
            json={
                "username": self.username,
                "otp_code": otp_code
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.service_token = data['service_token']
            self.device_token = data['admin']['device_token']
            self.save_token()
            print("? Bot authenticated successfully!")
            return True
        else:
            print(f"? OTP verification failed: {response.json()}")
            return False
    
    def check_status(self):
        """Check if admin is still active"""
        if not self.service_token:
            print("? No service token. Please authenticate first.")
            return False
        
        response = requests.get(
            f"{self.base_url}/bot/auth/check",
            params={
                "username": self.username,
                "service_token": self.service_token
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['is_active']:
                print(f"? Admin {self.username} is active")
                return True
            else:
                print(f"?? Admin {self.username} is disabled")
                return False
        else:
            print(f"? Status check failed: {response.json()}")
            return False
    
    def authenticate(self):
        """Complete authentication flow"""
        # Try to load existing token
        if self.load_token():
            # Verify token still valid
            if self.check_status():
                return True
            print("?? Saved token invalid, re-authenticating...")
        
        # Request new OTP
        if not self.request_otp():
            return False
        
        # Wait for user to enter OTP
        otp_code = input("Enter OTP from Telegram: ")
        
        # Verify OTP
        return self.verify_otp(otp_code)

# Usage
def main():
    bot = TelegramBotAuth(
        base_url="http://localhost:8000",
        username="admin"
    )
    
    # Authenticate (once)
    if bot.authenticate():
        print("?? Bot is ready!")
        
        # Periodic status check (every 5 minutes)
        while True:
            if not bot.check_status():
                print("?? Admin disabled, stopping bot...")
                break
            
            # Do bot work here
            print("?? Bot working...")
            
            # Wait 5 minutes
            time.sleep(300)
    else:
        print("? Authentication failed")

if __name__ == "__main__":
    main()
```

### Node.js Bot Example

```javascript
const axios = require('axios');
const fs = require('fs');
const readline = require('readline');

class TelegramBotAuth {
    constructor(baseUrl, username, tokenFile = 'bot_token.json') {
        this.baseUrl = baseUrl;
        this.username = username;
        this.tokenFile = tokenFile;
        this.serviceToken = null;
        this.deviceToken = null;
    }
    
    loadToken() {
        if (fs.existsSync(this.tokenFile)) {
            const data = JSON.parse(fs.readFileSync(this.tokenFile, 'utf8'));
            this.serviceToken = data.service_token;
            this.deviceToken = data.device_token;
            console.log('? Token loaded from file');
            return true;
        }
        return false;
    }
    
    saveToken() {
        fs.writeFileSync(this.tokenFile, JSON.stringify({
            service_token: this.serviceToken,
            device_token: this.deviceToken,
            username: this.username
        }));
        console.log('? Token saved to file');
    }
    
    async requestOTP() {
        try {
            const response = await axios.post(
                `${this.baseUrl}/bot/auth/request-otp`,
                { username: this.username }
            );
            console.log('? OTP sent to Telegram');
            return true;
        } catch (error) {
            console.error('? Failed to request OTP:', error.response?.data);
            return false;
        }
    }
    
    async verifyOTP(otpCode) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/bot/auth/verify-otp`,
                {
                    username: this.username,
                    otp_code: otpCode
                }
            );
            
            this.serviceToken = response.data.service_token;
            this.deviceToken = response.data.admin.device_token;
            this.saveToken();
            console.log('? Bot authenticated successfully!');
            return true;
        } catch (error) {
            console.error('? OTP verification failed:', error.response?.data);
            return false;
        }
    }
    
    async checkStatus() {
        if (!this.serviceToken) {
            console.error('? No service token. Please authenticate first.');
            return false;
        }
        
        try {
            const response = await axios.get(`${this.baseUrl}/bot/auth/check`, {
                params: {
                    username: this.username,
                    service_token: this.serviceToken
                }
            });
            
            if (response.data.is_active) {
                console.log(`? Admin ${this.username} is active`);
                return true;
            } else {
                console.warn(`?? Admin ${this.username} is disabled`);
                return false;
            }
        } catch (error) {
            console.error('? Status check failed:', error.response?.data);
            return false;
        }
    }
    
    async authenticate() {
        // Try to load existing token
        if (this.loadToken()) {
            if (await this.checkStatus()) {
                return true;
            }
            console.warn('?? Saved token invalid, re-authenticating...');
        }
        
        // Request new OTP
        if (!await this.requestOTP()) {
            return false;
        }
        
        // Wait for OTP input
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
        
        return new Promise((resolve) => {
            rl.question('Enter OTP from Telegram: ', async (otpCode) => {
                rl.close();
                resolve(await this.verifyOTP(otpCode));
            });
        });
    }
}

// Usage
async function main() {
    const bot = new TelegramBotAuth('http://localhost:8000', 'admin');
    
    if (await bot.authenticate()) {
        console.log('?? Bot is ready!');
        
        // Periodic status check
        setInterval(async () => {
            if (!await bot.checkStatus()) {
                console.error('?? Admin disabled, stopping bot...');
                process.exit(1);
            }
            console.log('?? Bot working...');
        }, 5 * 60 * 1000); // 5 minutes
    } else {
        console.error('? Authentication failed');
        process.exit(1);
    }
}

main();
```

---

## Examples

### Quick Start Script

**authenticate_bot.sh:**
```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
USERNAME="admin"

# Step 1: Request OTP
echo "Requesting OTP..."
curl -X POST "$BASE_URL/bot/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\"}"

# Step 2: Get OTP from user
echo ""
read -p "Enter OTP from Telegram: " OTP_CODE

# Step 3: Verify OTP
echo "Verifying OTP..."
RESPONSE=$(curl -X POST "$BASE_URL/bot/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"otp_code\":\"$OTP_CODE\"}")

# Extract service token
SERVICE_TOKEN=$(echo $RESPONSE | jq -r '.service_token')

# Save token
echo "{\"service_token\":\"$SERVICE_TOKEN\",\"username\":\"$USERNAME\"}" > bot_token.json

echo "? Authentication complete! Token saved to bot_token.json"
```

### Status Check Script

**check_status.sh:**
```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
USERNAME=$(jq -r '.username' bot_token.json)
SERVICE_TOKEN=$(jq -r '.service_token' bot_token.json)

curl -X GET "$BASE_URL/bot/auth/check?username=$USERNAME&service_token=$SERVICE_TOKEN"
```

---

## Troubleshooting

### Common Issues

#### 1. OTP Not Received

**Problem:** OTP not arriving in Telegram

**Solutions:**
- Check Telegram Bot 4 configuration
- Verify `telegram_2fa_chat_id` in admin account
- Check server logs for errors
- Ensure bot has permission to send messages

```bash
# Check admin's Telegram config
curl -X GET "http://localhost:8000/admin/admin" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"

# Look for:
# "telegram_2fa_chat_id": "123456789"
```

#### 2. Invalid OTP

**Problem:**
```json
{
  "detail": "Invalid or expired OTP"
}
```

**Solutions:**
- OTP expires in 5 minutes
- Request new OTP
- Check for typos
- Ensure using correct username

#### 3. Service Token Invalid

**Problem:**
```json
{
  "detail": "Invalid service token"
}
```

**Solutions:**
- Token may be corrupted
- Re-authenticate to get new token
- Check token saved correctly
- Verify not using interactive token by mistake

#### 4. Admin Disabled

**Problem:**
```json
{
  "is_active": false,
  "message": "Admin account is disabled"
}
```

**Solutions:**
- Contact Super Admin
- Check account expiry
- Verify not manually disabled
- Request re-activation

#### 5. Token Not Saved

**Problem:** Bot requires authentication every time

**Solutions:**
- Check file permissions
```bash
chmod 644 bot_token.json
```
- Verify file path correct
- Ensure disk not full
- Check for write errors

---

## Security Best Practices

### Token Storage

**Do:**
- ? Store in secure file with restricted permissions
- ? Use environment variables in production
- ? Encrypt token file
- ? Use secrets management (Vault, AWS Secrets Manager)

**Don't:**
- ? Commit token to git
- ? Store in plain text in public location
- ? Share token between bots
- ? Log token in plain text

### Token Management

**Rotation:**
```python
# Periodic token refresh (every 90 days)
if token_age > 90_days:
    bot.request_otp()
    bot.verify_otp(new_otp)
```

**Revocation:**
- Only revoked if admin disabled
- No manual revocation endpoint
- Contact Super Admin to disable admin

### Status Checking

**Frequency:**
```python
# Good: Check every 5 minutes
time.sleep(300)

# Too frequent: Every 10 seconds (unnecessary load)
time.sleep(10)

# Too infrequent: Every hour (slow to detect disabled admin)
time.sleep(3600)
```

### Error Handling

```python
def check_status_with_retry():
    max_retries = 3
    for i in range(max_retries):
        try:
            return bot.check_status()
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                time.sleep(10)
                continue
            raise
```

---

## Production Deployment

### Environment Variables

```bash
# .env
BOT_SERVICE_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
BOT_USERNAME=admin
BOT_DEVICE_TOKEN=abc123...
API_BASE_URL=https://api.example.com
```

### Docker Setup

```dockerfile
FROM python:3.10

# Copy bot code
COPY bot.py /app/

# Install dependencies
RUN pip install requests

# Set environment variables
ENV BOT_USERNAME=admin
ENV API_BASE_URL=http://backend:8000

# Run bot
CMD ["python", "/app/bot.py"]
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bot-credentials
type: Opaque
stringData:
  service_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  username: admin
  device_token: abc123...
```

---

## Summary

### Key Points

1. **One-time Setup:** Authenticate once, use forever
2. **Permanent Tokens:** No expiry, no re-authentication
3. **No Session Control:** Bypass single-session restrictions
4. **Auto-disable Only:** Only invalidated if admin disabled
5. **Periodic Checks:** Verify admin status regularly

### Authentication Steps

1. Request OTP ? `/bot/auth/request-otp`
2. Receive OTP ? Telegram Bot 4
3. Verify OTP ? `/bot/auth/verify-otp`
4. Save Token ? Store securely
5. Check Status ? `/bot/auth/check` (every 5 min)

### Best Practices

- Store token securely
- Check status periodically (5 min)
- Handle errors gracefully
- Log authentication events
- Monitor bot health

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
