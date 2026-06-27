# Brand icon

Neutral hub-and-spoke motif (a pool aggregating its workers) on a teal→blue tile.
Deliberately generic — no Braiins logo/trademark.

| File | Size |
|---|---|
| `icon.png` | 256×256 |
| `icon@2x.png` | 512×512 |

## How HA picks this up (HA ≥ 2026.3)

There is **no** `home-assistant/brands` PR anymore — that repo no longer accepts
custom-integration icons (a bot closes such PRs). Custom integrations ship their
own icon **here**, at `custom_components/braiins_pool/brand/`, and Home Assistant
serves it automatically via the **Brands Proxy API**
(`/api/brands/integration/braiins_pool/icon.png`). A local `brand/` folder takes
precedence over the CDN — nothing to submit.

A `403` on the icon just means a stale/missing proxy token → reload the page; it
is **not** an integration bug and is **not** fixed by removing this folder.

Ref: https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/
