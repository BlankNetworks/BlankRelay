# BlankRelay

BlankRelay is the relay backend for the Blank messaging and identity network.

It supports:

* relay-based messaging
* prekey upload and fetch
* queued message envelopes
* decentralized identity ledger scaffolding
* relay discovery
* join mode and sync gating
* sync slot capacity control
* operator-safe admin controls

⸻

# Setup Guide

This guide walks you through three steps:

1. Setting up a relay domain (DDNS)
2. Installing and running your relay
3. Connecting your relay to the Blank app

⸻

## Part 1 — Set Up a Relay Domain (DDNS)

Your relay needs a public address so devices and other relays can reach it.

Go to the DuckDNS website:
https://www.duckdns.org

Sign in using Google or GitHub.

Create a domain name. For example:
yourrelay.duckdns.org

Save this domain. You will use it during setup.

You may also see a DuckDNS token. Keep it saved, but it is not required for the basic relay setup.

⸻

## Part 2 — Install and Run Your Relay

On your Linux machine, install BlankRelay using the installer script from GitHub.

Download and run the installer from:
https://github.com/BlankNetworks/BlankRelay

Follow the instructions in the repository to run the installer script.

During setup, you will be asked for:

Relay domain
Enter the domain you created earlier, for example:
yourrelay.duckdns.org

Admin token
You can either:

* press Enter to generate one automatically
* or enter your own secure token

This admin token is private and should never be shared.

After installation, your relay will start automatically.

⸻

#nVerify your relay

Open a browser or use any HTTP tool and visit:

http://127.0.0.1:8080/health

You should see a response indicating the relay is running.

⸻

Port configuration (very important)

BlankRelay runs locally on port 8080.

To make your relay accessible from the internet, you must configure your router.

# Forward:

* external port 443
* to internal port 8080 on your relay machine

This allows your relay to be accessed using your domain without showing a port number.

⸻

# Test public access

Open in a browser:

http://yourrelay.duckdns.org

If everything is set correctly, you should see a healthy response.

⸻

Part 3 — Connect Relay to the Blank App

Once your relay is running and publicly accessible, you can connect it to the Blank app.

In the app:

1. Go to relay settings or add relay
2. Enter your relay address:

http://yourrelay.duckdns.org

3. Save the relay

⸻

# Test the connection

Register a test user through the app.

Your relay will:

* accept the registration
* store identity data
* process messages

If registration succeeds, your relay is fully working.

⸻

Local vs Public Access

There are two ways to access your relay:

Local (on the machine):
http://127.0.0.1:8080

Public (through your domain):
http://yourrelay.duckdns.org

⸻

## Security Notes

* Never share your admin token
* Never upload your .env file to GitHub
* Use a strong admin token
* Keep your system updated
