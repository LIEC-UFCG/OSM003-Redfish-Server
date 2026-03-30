import readings
from copy import deepcopy

def dynamic_eth_funcs():
    """
    Dynamically generates endpoint functions for each Ethernet interface detected in the system.

    Each function returns the Redfish dictionary corresponding to a specific network interface,
    allowing dynamic creation of Flask routes for each interface.

    Returns:
        list: List of functions, each returning the Redfish JSON for an Ethernet interface.
    """
    systems_eth_endpoint_functions = []
    interface_counter = 1

    for member in readings.eth_names():

        def bind_interface_function():
            iface_name = deepcopy(member)
            iface_number = str(deepcopy(interface_counter))

            def interface_function():
                stats = readings.eth_stats(iface_name)

                interface = {
                    "@odata.type": "#EthernetInterface.v1_12_3.EthernetInterface",
                    "Id": iface_name,
                    "Name": f"Ethernet Interface {iface_name}",
                    "Description": f"System NIC {iface_number}",
                    "FullDuplex": bool(stats['full_duplex']),  # Ensures it is boolean
                    "IPv4Addresses": stats['ipv4_addresses'],
                    "IPv6Addresses": stats['ipv6_addresses'],
                    "LinkStatus": stats['link_status'],
                    "MACAddress": stats['mac_address'],
                    "SpeedMbps": int(stats['speed_mbps']) if isinstance(stats['speed_mbps'], str) and stats['speed_mbps'].isdigit() else stats['speed_mbps'],
                    "Status": {"State": stats['state']},
                    #"Gateway": stats.get('gateway', "0.0.0.0"),  # If missing, assumes "0.0.0.0"
                    "NameServers": stats['dns'],
                    "@odata.context": "/redfish/v1/$metadata#EthernetInterface.EthernetInterface",  # Corrected
                    "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/EthernetInterfaces/{iface_name}",
                }
                return interface

            interface_function.__name__ = iface_name
            return interface_function

        systems_eth_endpoint_functions.append(bind_interface_function())
        interface_counter += 1

    return systems_eth_endpoint_functions

   

def get_computersystem_id_ethernetInterfaces():
    """
    Returns all Ethernet network interfaces of the system in Redfish format.

    Returns:
        dict: Redfish dictionary with the Ethernet interface collection with references to members.
    """
    machine_id = readings.machine_id()
    member_refs = []
    
    for iface in readings.eth_names():
        member_refs.append({
            "@odata.id": f"/redfish/v1/Systems/{machine_id}/EthernetInterfaces/{iface}"
        })

    response = {
        "@odata.type": "#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "@odata.id": f"/redfish/v1/Systems/{machine_id}/EthernetInterfaces",
        "Name": "Ethernet Interfaces Collection",
        "Description": "System NICs on Raspberry Pi",
        "Members@odata.count": len(member_refs),
        "Members": member_refs,
    }

    return response

