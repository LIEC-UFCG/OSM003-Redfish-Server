import json
import os


def _to_bool(value, default):
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in ("1", "true", "yes", "on"):
			return True
		if normalized in ("0", "false", "no", "off"):
			return False
	return default


DEFAULT_CONFIG = {
	"FLASK_PORT": 5004,
	"FLASK_IP": "0.0.0.0",
	"CERT_FILE": "domainSAN.crt",
	"KEY_FILE": "domain.key",
	"SESSION_TIMEOUT": 60 * 60,
	"DCN_ID": "DCN1",
	"ENABLE_RATE_LIMIT": True,
	"RATE_LIMIT": "1 per second",
	"ALLOW_MULTIPLE_SESSIONS": True,
	"ENABLE_DOCKER_GROUP": False,
	"RUN_SERVER_AFTER_SETUP": False,
	"POWER_CAPACITY_WATTS": 250,
	"POWER_ALLOCATED_WATTS": 0,
}


def _load_file_config(config_file_path):
	if not os.path.exists(config_file_path):
		return {}
	try:
		with open(config_file_path, "r", encoding="utf-8") as file:
			loaded = json.load(file)
			return loaded if isinstance(loaded, dict) else {}
	except Exception:
		return {}


CONFIG_FILE = os.getenv("REDFISH_SERVER_CONFIG_FILE", "server_config.json")
FILE_CONFIG = _load_file_config(CONFIG_FILE)


def _get(name):
	env_value = os.getenv(name)
	if env_value is not None:
		return env_value
	return FILE_CONFIG.get(name, DEFAULT_CONFIG[name])


# Port where Flask will run
FLASK_PORT = int(_get("FLASK_PORT"))

# Flask listen IP (0.0.0.0 accepts connections from any interface)
FLASK_IP = str(_get("FLASK_IP"))

# Path to SSL certificate file
CERT_FILE = str(_get("CERT_FILE"))

# Path to SSL private key file
KEY_FILE = str(_get("KEY_FILE"))

# Session expiration time in seconds
SESSION_TIMEOUT = int(_get("SESSION_TIMEOUT"))

DCN_ID = str(_get("DCN_ID"))

# Rate limiting runtime settings
ENABLE_RATE_LIMIT = _to_bool(_get("ENABLE_RATE_LIMIT"), True)
RATE_LIMIT = str(_get("RATE_LIMIT"))

# Session creation policy
ALLOW_MULTIPLE_SESSIONS = _to_bool(_get("ALLOW_MULTIPLE_SESSIONS"), True)

# Setup helpers (used by setup_source.sh)
ENABLE_DOCKER_GROUP = _to_bool(_get("ENABLE_DOCKER_GROUP"), False)
RUN_SERVER_AFTER_SETUP = _to_bool(_get("RUN_SERVER_AFTER_SETUP"), False)

# Power defaults used when hardware readings are unavailable
POWER_CAPACITY_WATTS = float(_get("POWER_CAPACITY_WATTS"))
POWER_ALLOCATED_WATTS = float(_get("POWER_ALLOCATED_WATTS"))