import readings
from copy import deepcopy

def dynamic_eth_funcs():
    """
    Gera dinamicamente funções de endpoint para cada interface Ethernet detectada no sistema.

    Cada função retornará o dicionário Redfish correspondente à interface de rede específica,
    permitindo a criação dinâmica de rotas Flask para cada interface.

    Returns:
        list: Lista de funções, cada uma retornando o JSON Redfish de uma interface Ethernet.
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
                    "FullDuplex": bool(stats['full_duplex']),  # Garante que seja booleano
                    "IPv4Addresses": stats['ipv4_addresses'],
                    "IPv6Addresses": stats['ipv6_addresses'],
                    "LinkStatus": stats['link_status'],
                    "MACAddress": stats['mac_address'],
                    "SpeedMbps": int(stats['speed_mbps']) if isinstance(stats['speed_mbps'], str) and stats['speed_mbps'].isdigit() else stats['speed_mbps'],
                    "Status": {"State": stats['state']},
                    #"Gateway": stats.get('gateway', "0.0.0.0"),  # Se não existir, assume "0.0.0.0"
                    "NameServers": stats['dns'],
                    "@odata.context": "/redfish/v1/$metadata#EthernetInterface.EthernetInterface",  # Corrigido
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
    Retorna todas as interfaces de rede Ethernet do sistema no formato Redfish.

    Returns:
        dict: Dicionário Redfish com a coleção de interfaces Ethernet, incluindo detalhes de cada interface.
    """
    interfaces = []
    
    for iface in readings.eth_names():
        stats = readings.eth_stats(iface)

        interface_data = {
            "@odata.type": "#EthernetInterface.v1_12_3.EthernetInterface",
            "Id": iface,
            "Name": f"Ethernet Interface {iface}",
            "Description": f"Network Interface {iface}",
            "FullDuplex": bool(stats['full_duplex']),  # Garante que seja booleano
            "IPv4Addresses": stats.get('ipv4_addresses', []),  # Lista vazia se não existir
            "IPv6Addresses": stats.get('ipv6_addresses', []),
            "LinkStatus": stats.get('link_status', "Unknown"),
            "MACAddress": stats.get('mac_address', "00:00:00:00:00:00"),
            "SpeedMbps": int(stats['speed_mbps']) if isinstance(stats['speed_mbps'], str) and stats['speed_mbps'].isdigit() else stats['speed_mbps'],
            "Status": {"State": stats.get('state', "Enabled")},
            #"Gateway": stats.get('gateway', "0.0.0.0"),  # Se não existir, assume "0.0.0.0"
            "NameServers": stats.get('dns', []),
            "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/EthernetInterfaces/{iface}",
        }
        
        interfaces.append(interface_data)

    response = {
        "@odata.type": "#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "@odata.context": "/redfish/v1/$metadata#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/EthernetInterfaces",
        "Name": "Ethernet Interfaces Collection",
        "Description": "System NICs on Raspberry Pi",
        "Members@odata.count": len(interfaces),
        "Members": interfaces,  # Lista correta de interfaces
    }

    return response

