# VM Network Reconfiguration for HTTPS Deployment

This document describes the steps taken to migrate a VirtualBox Linux VM from a NAT‑only configuration to a dual‑adapter setup, enabling HTTPS through IIS while maintaining temporary NAT connectivity. After validation, the VM transitions fully to the bridged network.

---

## 1. Add and Configure Adapter 2 (Bridged Mode)

A second network adapter was added to the VM using Bridged Adapter mode.
This adapter provides the VM with a real LAN address (e.g., `192.168.0.x`), enabling:

- IIS HTTPS binding to a LAN‑reachable IP
- Certificate creation and validation
- Direct access to the Flask application from the local network

After enabling Adapter 2, the VM obtained a LAN IP such as:

```txt
192.168.0.3
```

This IP becomes the primary endpoint for HTTPS.

---
## 2. Keep Adapter 1 (NAT) Enabled Temporarily

Adapter 1 remained active during the transition because:

- Existing port‑forwarding rules were still required (see below)
- Flask and PostgreSQL were communicating through the NAT (`10.0.2.x → 10.0.0.1`)
- Keeping NAT active ensured no service interruption while HTTPS was configured

During this phase, the VM had two active interfaces:
cd
- `10.0.2.15` (NAT)
- `192.168.0.3` (Bridged)

This dual‑adapter setup allowed HTTPS configuration without breaking the existing application.

### Port Forwarding Rules on Adapter 1

| Name        | Protocol | Host IP        | Host Port | Guest IP     | Guest Port |
|-------------|----------|----------------|-----------|--------------|------------|
| Canoa       | TCP      | 192.168.0.101  | 1995      | 10.0.2.15    | 5001       |
| CanoaStage  | TCP      | 192.168.0.101  | 1997      | 10.0.2.15    | 5007       |
| Putty       | TCP      | 192.168.0.101  | 1996      | 10.0.2.15    | 22         |


---

## 3. Update Flask to Listen on the Adapter 2 IP

Once HTTPS was configured on IIS using the LAN IP and Adapter 1 was disabled,
Flask was updated to bind to all interfaces (0.0.0.0),
ensuring it remained reachable through the bridged network.


After confirming that Flask was reachable through Adapter 2:

- PostgreSQL access was updated to use the host’s LAN IP (192.168.0.101)
- The dependency on VirtualBox NAT routing was removed

- Adapter 1 (NAT) could then be safely disabled
- This results in a cleaner, more stable network architecture.

## 4. Update PuTTY to Use Adapter 2

With Adapter 1 disabled, SSH access must use the VM’s LAN IP.

Steps:

1. Open PuTTY
2. Set Host Name to the VM’s bridged IP: `192.168.0.3`
3. Save the session profile
4. Connect normally through the LAN

This completes the migration from NAT‑based access to LAN‑based access.


# Router Port Forwarding Rules

To support understanding of the internal network architecture, the following are the active port forwarding rules configured on the router. From any `External IP` to `Internal IP 192.168.0.101`

| Rule Name      | Protocol | External Port | Internal Port
|----------------|----------|---------------|---
| CPE-HTTP       | TCP      | 80            | 80
| CPE-Canoe      | TCP      | 45445         | 1995
| CPE-RDServer   | TCP      | 45145         | 3389
| CPE-Postgres   | TCP      | 45345         | 5432
| CPE-HTTPS      | TCP      | 443           | 443
| CPE-RDDisco    | TCP      | 45545         | 45545
| CPE-SQLServer  | TCP      | 45945         | 1433
| CPE-Lubunterm  | TCP      | 45645         | 1996
| CPE-WinTerm    | TCP      | 45245         | 22

---
<small>_eof_<small>

