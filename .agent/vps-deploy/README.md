# VPS deploy — spacetime-lab MCP bridge

End-to-end guide for Phase C of the dispatch-bridge: expose the PC's
local MCP server to `claude.ai` over a self-hosted WireGuard tunnel
and Caddy reverse proxy.

## Architecture

```
[claude.ai mobile / web]
        |  HTTPS
        v
[mcp.<your-domain>] --A--> [VPS public IP]
                                |
                       Caddy (Let's Encrypt, :443)
                                |
                    reverse_proxy to 10.8.0.2:8765
                                |
                       WireGuard tunnel (UDP :51820)
                                |
                                v
                        [PC at 10.8.0.2]
                        mcp_server.py on 10.8.0.2:8765
                        reads .agent/runs/_summary.jsonl + LATEST.md
                        via .agent/_wrapper/mcp_server.py
                        auth: X-MCP-Token header
```

Two boxes involved:

- **VPS** (ephemeral, public-facing, will run Caddy + WireGuard)
- **PC** (permanent, behind NAT, runs the MCP server + WireGuard client)

## Prereqs

1. **Domain**: something under your control (Cloudflare Registrar,
   Namecheap, Porkbun).  We only need one A record.
2. **VPS with public IPv4**: Oracle Cloud Free Tier (ARM, free forever),
   Fly.io hobby (free tier), Hetzner CAX11 (~€3.79/mo), DigitalOcean
   basic droplet ($4/mo).  Ubuntu 22.04 / 24.04 or Debian 12 + root SSH.
3. **PC-side WireGuard keypair**: already generated at
   `~/.spacetime-bridge/wg-pc-client-{private,public}.key` by
   `python .agent/_wrapper/wg_keygen.py`.
4. **MCP server token**: at `~/.spacetime-bridge/mcp-token`, generated
   by the Startup-folder launcher.

## Step-by-step

### 1. DNS in Cloudflare

In your Cloudflare dashboard, for your chosen subdomain (e.g.,
`mcp.chernandez.dev`):

- Type: **A**
- Name: `mcp` (or whichever subdomain)
- IPv4: your VPS public IP
- Proxy status: **DNS only** (grey cloud) — Caddy needs to handle TLS,
  not Cloudflare.  Turning on the orange cloud breaks the ACME HTTP-01
  challenge.
- TTL: Auto

Verify once created:
```bash
dig +short mcp.<your-domain>
# should print the VPS IP
```

### 2. On your PC, get the public WireGuard key

```bash
python .agent/_wrapper/wg_keygen.py --show
# example output: x+3MzNekqmFFscz22UuzBr+IwduJ3d0QH7NeVSQbiHM=
```

Save that string — it goes into the VPS config.

### 3. SSH into the VPS and run the deploy script

```bash
# From your PC (git-bash / wsl / anywhere with ssh):
scp .agent/vps-deploy/deploy-to-vps.sh user@VPS_IP:/tmp/
ssh user@VPS_IP
```

On the VPS:
```bash
sudo -E env \
  DOMAIN=mcp.<your-domain> \
  PC_CLIENT_PUBKEY='<pub key from step 2>' \
  ADMIN_EMAIL=you@example.com \
  bash /tmp/deploy-to-vps.sh
```

At the end the script prints the VPS's own WireGuard public key.
**Copy it** — you need it on the PC.

### 4. Install WireGuard on the PC (needs admin)

```powershell
# Elevated PowerShell:
winget install WireGuard.WireGuard
```

### 5. Configure the PC-side WireGuard tunnel

Open the WireGuard app → Add Tunnel → Add empty tunnel.  Paste:

```ini
[Interface]
PrivateKey = <contents of ~/.spacetime-bridge/wg-pc-client-private.key>
Address    = 10.8.0.2/24

[Peer]
PublicKey           = <VPS public key from step 3>
Endpoint            = <VPS public IP>:51820
AllowedIPs          = 10.8.0.1/32
PersistentKeepalive = 25
```

Save as `spacetime-bridge`.  Click **Activate**.

Verify the tunnel is up:
```bash
ping 10.8.0.1    # should get replies from the VPS inside the tunnel
```

### 6. Rebind the MCP server to the WireGuard IP

Edit `~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/mcp-bridge-server.cmd`
and change:
```
set MCP_BIND=127.0.0.1:8765
```
to:
```
set MCP_BIND=10.8.0.2:8765
```

Restart the MCP server:
```powershell
Get-Process python | Where-Object { $_.MainWindowTitle -match 'MCP' } | Stop-Process
# then double-click the launcher or log out + back in
```

### 7. Verify end-to-end from the internet

From your phone's LTE (or any external network), hit the public URL:

```bash
TOKEN=$(cat ~/.spacetime-bridge/mcp-token)
curl -v https://mcp.<your-domain>/mcp \
    -H "X-MCP-Token: $TOKEN" \
    -H "Accept: application/json, text/event-stream" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}'
```

Expected: HTTP 200, JSON-RPC response with `serverInfo.name =
spacetime-lab-dispatch`.  If you get 502, the tunnel is down.  If you
get 401, the token is wrong.  If you get 404, the path is wrong
(should be `/mcp`).

### 8. Register as Custom Connector in claude.ai

Settings → Connectors → Add custom connector:

- Name: Spacetime Lab Dispatch
- URL: `https://mcp.<your-domain>`
- Custom headers: `X-MCP-Token: <your token>`
- Test → the 3 tools should appear

### 9. Use from claude.ai mobile

Open any new conversation in claude.ai.  Ask: _"use the spacetime-lab
dispatch tools to tell me what happened in the last dispatch"_.
Expected: it invokes `get_latest_dispatch()` and reads back the
briefing from your PC.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| ACME challenge failing | Cloudflare proxy is orange, not grey | Change to DNS-only |
| 502 Bad Gateway from Caddy | WG tunnel down or MCP server not bound to 10.8.0.2 | Check `wg show` on both ends; check `MCP_BIND` on PC |
| 401 from MCP server | Token mismatch | `cat ~/.spacetime-bridge/mcp-token` matches the header claude.ai sends |
| claude.ai says connector failed | Cert not issued yet | Wait 30-60s after first hit; check `journalctl -u caddy -f` |
| WG tunnel up but can't reach 10.8.0.1 | IP forwarding or iptables | `sysctl net.ipv4.ip_forward` must be 1; check PostUp rules |

## Security notes

- The token in `~/.spacetime-bridge/mcp-token` is the only thing
  protecting your server from random internet scanners.  Keep it
  secret.  Rotate if leaked.  Generate a new one with
  `python -c "import secrets; print(secrets.token_urlsafe(32))"` and
  restart the MCP server.
- The tunnel only allows `10.8.0.1 ↔ 10.8.0.2` traffic; the rest of the
  internet is NOT routed through your PC (despite the MASQUERADE rule,
  which only applies to packets EXITING the VPS's public interface,
  not inbound).
- Caddy auto-renews Let's Encrypt certs every 60 days.  No action
  needed from you.
