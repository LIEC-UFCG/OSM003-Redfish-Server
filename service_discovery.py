from ssdpy import SSDPServer
import socket, re
from config import FLASK_PORT, DCN_ID
from readings import cpu_model, system_uuid


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

def discovery_SSDP():
    """
    Starts the SSDP service for device discovery on the network.

    Uses the local IP address and configured port to advertise the service via SSDP.

    Side Effects:
        Starts the SSDP server and prints to console the location address of the service.
    """
    
    local_ip = get_local_ip()
    last_octet = local_ip.split(".")[-1] if "." in local_ip else re.sub(r"\D", "", local_ip)[-3:]
    last_octet = last_octet.zfill(3)[-3:]
    model = cpu_model()
    device_name = f"{model}-{last_octet}"

    device_type = "urn:dmtf-org:service:redfish-rest:1"

    location = f"https://{local_ip}:{FLASK_PORT}/redfish/v1/"
    server = SSDPServer(
        device_name,
        device_type=device_type,
        location=location
    )
    print(f"SSDP server started with location: {location}")
    server.serve_forever()