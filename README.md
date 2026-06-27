# Braiins Pool — Home Assistant integration

A small, clean Home Assistant integration that reads **pool-side** mining stats
from the [Braiins Pool](https://pool.braiins.com/) account API and exposes them
as sensors (account totals + per-worker hashrate).

This is **read-only** monitoring — it never controls the pool or the miners.
For miner control use a miner integration (e.g. hass-miner); this surfaces what
actually *arrives at the pool*, which a miner can't tell you on its own.

## Why this exists

The one community component that existed (`tomlac40/braiins`) was a YAML-platform
sensor that disabled TLS verification and never set entity state. This is a clean
rewrite: config flow, a `DataUpdateCoordinator`, proper sensors/units, no extra
Python dependencies (uses Home Assistant's own HTTP client).

## Install (HACS, custom repository)

1. HACS → ⋮ → Custom repositories → add `https://github.com/pos-ei-don/ha-braiins-pool`, category **Integration**.
2. Install **Braiins Pool**, restart Home Assistant.
3. Settings → Devices & Services → **Add Integration** → *Braiins Pool*.
4. Paste a **read-only API token** (pool.braiins.com → Account → Access Profiles).

## Sensors (v0.1)

**Account** (device *Braiins Pool (&lt;username&gt;)*): hashrate 5m / 60m / 24h
(TH/s), balance, today reward, all-time reward (BTC), workers OK.

**Per worker** (present at setup): 5m hashrate, 24h hashrate (TH/s), state.

## Roadmap

Further features are collected in the tracking ticket — see
`pos-ei-don/ai_mainprojekt`. Likely next: dynamic worker add/remove, pool-wide
stats (network/fpps), options for scan interval, value-template-friendly raw
attributes, multiple coins.

## License

MIT — see [LICENSE](LICENSE).
