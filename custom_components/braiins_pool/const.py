"""Constants for the Braiins Pool integration."""

from __future__ import annotations

DOMAIN = "braiins_pool"

CONF_API_TOKEN = "api_token"
CONF_SCAN_INTERVAL = "scan_interval"

API_BASE = "https://pool.braiins.com"
PROFILE_EP = "/accounts/profile/json/btc/"
WORKERS_EP = "/accounts/workers/json/btc/"

# Pool stats update on the order of minutes; 5 min keeps it light + read-only.
DEFAULT_SCAN_INTERVAL = 300

# Braiins reports hashrate in Gh/s; we surface TH/s.
GH_TO_TH = 1000.0
