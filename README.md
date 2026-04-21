# BlankRelay

BlankRelay is the relay backend for the Blank messaging and identity network.

---

# 🚀 Setup Guide

This guide walks you through:

1. Setting up a DDNS (your relay address)
2. Installing your relay
3. Connecting your relay to the Blank app

---

# 🌐 Part 1 — Set Up a DDNS (DuckDNS)

Your relay needs a public address so users and other relays can reach it.

## Step 1

Go to:

https://www.duckdns.org

## Step 2

Sign in using:
- Google
- GitHub

## Step 3

Create a domain.

Example: yourrelay.duckdns.org

## Step 4

Save:
- your domain (you will use this in setup)
- your DuckDNS token (you may use later for auto-IP updates)

---

# ⚙️ Part 2 — Install Your Relay

## One-command install (recommended)

Run this on your Linux machine:

```bash
curl -fsSL https://raw.githubusercontent.com/BlankNetworks/BlankRelay/main/install_blankrelay.sh

During install you will be asked:

Relay domain

Enter your DuckDNS domain: yourrelay.duckdns.org

Admin token

You can:

* press ENTER to auto-generate (recommended)
* or paste your own secure token

Example token: a long random string (do not share this)

After install

Verify your relay is running

Run: curl http://127.0.0.1:8080/health

Expected: {"status":"ok"}


IMPORTANT — Port Forwarding

You must open your relay to the internet. http://127.0.0.1:8080/health is for LOCAL testing, your relay machine will need to open port 443 for HTTPS connections externally.

On your router:

* Port: 443
* Protocol: TCP
* Forward to: your machine’s local IP


Test externally

Open in browser: http://yourrelay.duckdns.org:8080/health

If you see: {"status":"ok"} , Your relay is live.

---

# 📱 Part 3 — Connect Relay to Blank App
