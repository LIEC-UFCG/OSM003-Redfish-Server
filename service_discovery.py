import random
import socket
import time
import uuid

from config import FLASK_PORT
from readings import machine_id, system_uuid


SSDP_MULTICAST_ADDR = "239.255.255.250"
SSDP_PORT = 1900
MAX_AGE_SECONDS = 1800
REDFISH_ST_BASE = "urn:dmtf-org:service:redfish-rest:1"


def get_local_ip():
    """
    Gets the local IP address of the Raspberry Pi.

    Returns:
        str: Local IP address detected.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def _parse_ssdp_headers(raw_packet):
    """Parse an incoming SSDP datagram and return lowercase header keys.

    Args:
        raw_packet (bytes): Raw UDP payload received on SSDP socket.

    Returns:
        dict | None: Parsed headers when packet is M-SEARCH, otherwise None.
    """
    text = raw_packet.decode("utf-8", errors="ignore")
    lines = text.split("\r\n")
    if not lines or not lines[0].startswith("M-SEARCH"):
        return None

    headers = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _service_uuid():
    """Return the stable UUID used in SSDP USN.

    Prefers the Redfish service UUID and uses a deterministic fallback
    derived from machine ID when unavailable.

    Returns:
        str: UUID string in canonical format.
    """
    svc_uuid = system_uuid()
    if svc_uuid:
        return str(svc_uuid).strip()

    # Deterministic fallback when system UUID is unavailable.
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_id()))


def _response_st(requested_st):
    """Choose the ST value for response based on incoming M-SEARCH target.

    Args:
        requested_st (str): Search target received from client.

    Returns:
        str: Response ST honoring Redfish base target semantics.
    """
    if requested_st.startswith("urn:dmtf-org:service:redfish-rest:1"):
        return requested_st
    return REDFISH_ST_BASE


def _build_msearch_response(local_ip, requested_st):
    """Build a Redfish-compliant SSDP M-SEARCH response payload.

    Args:
        local_ip (str): Local IPv4 address used by the Redfish service.
        requested_st (str): Search target from incoming request.

    Returns:
        bytes: HTTP/1.1 200 OK SSDP response bytes.
    """
    service_root = f"https://{local_ip}:{FLASK_PORT}/redfish/v1/"
    response_st = _response_st(requested_st)
    usn = f"uuid:{_service_uuid()}::{REDFISH_ST_BASE}"

    # Redfish DSP0266 12.4.4 response shape for M-SEARCH.
    payload = (
        "HTTP/1.1 200 OK\r\n"
        f"CACHE-CONTROL: max-age={MAX_AGE_SECONDS}\r\n"
        f"ST: {response_st}\r\n"
        f"USN: {usn}\r\n"
        f"AL: {service_root}\r\n"
        f"LOCATION: {service_root}\r\n"
        "EXT:\r\n"
        "\r\n"
    )
    return payload.encode("utf-8")


def _should_respond(requested_st):
    """Check if incoming ST should receive a response from this service.

    Args:
        requested_st (str): Search target value from M-SEARCH.

    Returns:
        bool: True when target is supported by Redfish discovery behavior.
    """
    if not requested_st:
        return False
    st = requested_st.lower()
    return (
        st == "ssdp:all"
        or st == "upnp:rootdevice"
        or st.startswith("urn:dmtf-org:service:redfish-rest:1")
    )

def discovery_SSDP():
    """
    Starts a Redfish SSDP responder for M-SEARCH discovery on the network.

    Listens on UDP/1900 multicast, validates incoming M-SEARCH ST values,
    applies MX random delay, and responds with Redfish-compliant headers.

    Side Effects:
        Starts the SSDP server and prints to console the location address of the service.
    """
    
    local_ip = get_local_ip()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", SSDP_PORT))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    membership = socket.inet_aton(SSDP_MULTICAST_ADDR) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)

    print(f"SSDP responder started on {SSDP_MULTICAST_ADDR}:{SSDP_PORT} (service root https://{local_ip}:{FLASK_PORT}/redfish/v1/)")

    while True:
        data, addr = sock.recvfrom(2048)
        headers = _parse_ssdp_headers(data)
        if not headers:
            continue

        requested_st = headers.get("st", "")
        if not _should_respond(requested_st):
            continue

        # Honor MX random delay recommendation for M-SEARCH responses.
        try:
            mx = int(headers.get("mx", "1"))
        except ValueError:
            mx = 1
        mx = max(0, min(mx, 5))
        if mx > 0:
            time.sleep(random.uniform(0, mx))

        response = _build_msearch_response(local_ip, requested_st)
        sock.sendto(response, addr)