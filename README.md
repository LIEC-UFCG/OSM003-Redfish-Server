# LIEC Redfish Server

This repository contains the open-source implementation of a secure Redfish RESTful server, developed in Python using the Flask microframework. This project serves as the practical companion and case study for the paper: "Implementation Guide for Secure RESTful Asset Management APIs under IEC 62443-4-2: A Redfish Case Study".

The primary objective of this project is to demonstrate how abstract industrial cybersecurity requirements from the IEC 62443-4-2 Standard (Security Level 2) can be effectively mapped and implemented into a concrete, resource-constrained Operational Technology (OT) edge device, such as a Distributed Control Node (DCN).

---
**Intellectual Property Notice:** The core architecture of this implementation is derived from the software registered at the Brazilian National Institute of Industrial Property (INPI) under the ID **BR512025003471-7** ("IIoT Management System via Redfish").

## Citation
If you use this software in research, please cite it as described in [CITATION.cff](CITATION.cff).


## Core Capabilities & Security Controls

This project is built to function both as a robust asset management interface and as a hardened security case study. The features are divided into core operational capabilities and standards-based security controls.

### Core Redfish Capabilities
* **RESTful Architecture:** Fully functional Redfish REST API endpoints implemented with a modular design.
* **Industrial Edge Focus:** Lightweight and optimized for resource-constrained embedded devices and Distributed Control Nodes (DCNs).
* **Telemetry & Monitoring:** Real-time thermal and system metrics monitoring.
* **Network Visibility:** SSDP (Simple Service Discovery Protocol) support for automated device discovery.
* **Session Management:** Comprehensive lifecycle management for user sessions and API interactions.

### IEC 62443-4-2 Security Controls (SL2)
This implementation natively enforces several critical security capabilities, aligning with IEC 62443-4-2 Security Level 2 (SL2):

* **Identification & Authentication (FR 1):** Support for HTTP Basic Authentication and Token-based Session Authentication (`X-Auth-Token`). Implements `bcrypt` password hashing and account lockout mechanisms against brute-force attacks.
* **Use Control (FR 2):** Role-Based Access Control (RBAC) enforced via a Redfish Privilege Registry. Includes automated session timeouts and manual session locking.
* **System Integrity & Confidentiality (FR 3 & FR 4):** Mandatory HTTPS/TLS for API transport security.
* **Timely Response to Events (FR 6):** Structured, timestamped audit logging of all security-relevant events (authentication attempts, configuration changes, failures) to support centralized SIEM monitoring.
* **Resource Availability (FR 7):** Context-aware, per-client rate limiting implemented via `Flask-Limiter` to protect against Denial-of-Service (DoS) and resource exhaustion attacks.
---

## Installation & Execution

You can run the secure Redfish server using two different methods: running directly from the Python source code (recommended for development and testing) or building a standalone executable using PyInstaller (ideal for deployment on OT edge devices without a pre-installed Python environment).

### Prerequisites (both options)
- Python 3.10+ (install it first on fresh VMs)
- `pip`
- OpenSSL installed and available in PATH
- Docker Engine installed and running (required for container endpoints)
- (Linux) permissions to register certificates in the system trust store (uses `sudo`)

If Python is not installed yet:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### Clone the repository
```bash
git clone https://github.com/LIEC-UFCG/OSM003-Redfish-Server.git
cd OSM003-Redfish-Server
```

If you get `Permission denied` when accessing Docker (for example, `/var/run/docker.sock`):
```bash
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl enable --now docker
```

### Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Method 1: Running from Source (Development)

#### Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you prefer installing the core packages manually, you can use:
```bash
pip install Flask psutil py-cpuinfo bcrypt ssdpy docker apscheduler Flask-Limiter flask-talisman
```

#### Review configuration
Adjust runtime settings in [server_config.json](server_config.json) (recommended), or override with environment variables when needed.

Main options:
- `FLASK_IP`
- `FLASK_PORT`
- `CERT_FILE`
- `KEY_FILE`
- `ENABLE_RATE_LIMIT`
- `RATE_LIMIT`
- `ALLOW_MULTIPLE_SESSIONS`
- `SESSION_TIMEOUT`
- `ENABLE_DOCKER_GROUP` (used by `setup_source.sh`)
- `RUN_SERVER_AFTER_SETUP` (used by `setup_source.sh`)

#### Start the server
```bash
python main.py
```

On first run, if needed, the project attempts to generate certificates (`domainSAN.crt` / `domain.key`) based on the local IP.

### Method 2: Build with PyInstaller and run the binary

#### Install build dependency
```bash
pip install pyinstaller
```

#### Build

Build and package:
```bash
pip install -r requirements.txt
chmod +x build_and_package.sh
./build_and_package.sh
```

This generates `redfish_server_package.tar.gz`.

#### Final user run steps

For the final user (target machine):
```bash
tar -xzf redfish_server_package.tar.gz
chmod +x start.sh
./start.sh
```

`start.sh` selects the correct binary automatically based on architecture (`server_x86_64` or `server_arm`).

### Test the main endpoint
Open in your browser:
- `https://<IP-or-host>:5004/redfish/v1`

Or use curl (test environment):
```bash
curl -k https://127.0.0.1:5004/redfish/v1
```

## Accounts and session flow

This server uses Redfish-style accounts and sessions for protected endpoints.

### Existing accounts
- Accounts are stored in `accounts.json`.
- If `accounts.json` does not exist, the application seeds default accounts from code (`admin`, `user`, `teste`) in `manageraccount.py`.
- Passwords are stored as bcrypt hashes.

### Authentication model
- Protected endpoints require either:
	- `X-Auth-Token` (session token), or
	- HTTP Basic Auth (`Authorization: Basic ...`).
- Recommended flow for API clients: create a session and use `X-Auth-Token`.

### Step 1) Create a session (login)
```bash
curl -k -X POST https://127.0.0.1:5004/redfish/v1/SessionService/Sessions \
	-H "Content-Type: application/json" \
	-d '{"UserName":"admin","Password":"<your-password>"}' -i
```

On success, the response returns:
- Status `201 Created`
- Header `X-Auth-Token: <token>`
- Header `Location: /redfish/v1/SessionService/Sessions/<session_id>`

### Step 2) Use the token to access protected resources
```bash
curl -k https://127.0.0.1:5004/redfish/v1/AccountService \
	-H "X-Auth-Token: <token>"
```

### Step 3) List existing accounts
```bash
curl -k https://127.0.0.1:5004/redfish/v1/AccountService/Accounts \
	-H "X-Auth-Token: <token>"
```

### Step 4) Create a new account
Requires a role with privileges to manage `ManagerAccountCollection`.

```bash
curl -k -X POST https://127.0.0.1:5004/redfish/v1/AccountService/Accounts \
	-H "Content-Type: application/json" \
	-H "X-Auth-Token: <admin-or-privileged-token>" \
	-d '{
		"UserName":"newuser",
		"RoleId":"Operator",
		"Password":"@StrongPass123",
		"Enabled": true
	}'
```

### Step 5) Create a session with the new account
```bash
curl -k -X POST https://127.0.0.1:5004/redfish/v1/SessionService/Sessions \
	-H "Content-Type: application/json" \
	-d '{"UserName":"newuser","Password":"@StrongPass123"}' -i
```

### Step 6) Logout (delete session)
```bash
curl -k -X DELETE https://127.0.0.1:5004/redfish/v1/SessionService/Sessions/<session_id> \
	-H "X-Auth-Token: <token>"
```

Notes:
- Multiple sessions per user are allowed by default (Redfish-friendly).
- To enable optional hardening (single active session per user), set `ALLOW_MULTIPLE_SESSIONS` to `false` in [server_config.json](server_config.json).
- Account lockout and password constraints are enforced by AccountService settings.

---

## License
See [LICENSE](LICENSE).
