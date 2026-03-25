import readings
from copy import deepcopy
from flask import jsonify, request, make_response
import psutil
import cpuinfo
import subprocess
import json
import logging
from datetime import datetime
import threading

# pip install py-cpuinfo


def get_computer():
    """
    Returns the collection of computer systems.

    Returns:
        dict: Dictionary with computer systems collection information in Redfish format.
    """
    computer = {
        "@odata.type": "#ComputerSystemCollection.ComputerSystemCollection",
        "Name": "ComputerSystem Collection",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": "/redfish/v1/Systems/" + readings.machine_id()
            }
        ],
        "@odata.id": "/redfish/v1/Systems"
    }
    return computer

def get_computer_system():
    """
    Returns the details of ComputerSystem in Redfish format.

    Returns:
        flask.Response: JSON response with ComputerSystem details.
    """
    computer_id = {
        "@odata.type": "#ComputerSystem.v1_23_1.ComputerSystem",
        "Name": "ComputerSystem Collection",
        "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}",
        "Id": readings.machine_id(),
        "@odata.context": "/redfish/v1/$metadata#ComputerSystem.ComputerSystem",
        "EthernetInterfaces": {
            "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/EthernetInterfaces",
        },
        "HostedServices": {
            "DistributedControlNodeServices": {
                "@odata.id": "/redfish/v1/DistributedControlNode",
            }
        },
        
        #"IndicatorLED": readings.power_led(),
        "Links": {
            "Chassis": [
                {
                    "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id()
                }
            ],
            "ManagedBy": [
                {
                    "@odata.id": "/redfish/v1/Managers/" + readings.machine_id()
                }
            ]
        },
        "LogServices": {
            "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/LogServices"
        }, 
        "Manufacturer": readings.manufacturer(),  
        #"Memory": {
        #    "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Memory"
        #},
        "MemorySummary": {
            "Status": {
                "Health": readings.memory_health(),
                "State": "Enabled"
            },
            "TotalSystemMemoryGiB": readings.memory_total(),
        },
        "Model": readings.model(),
        "OperatingSystem": {
            "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/OperatingSystem"
        },
        "ProcessorSummary": {
            "Count": 1,  # Raspberry Pi has 1 physical processor
            "Model": readings.cpu_model(),  # Processor model
            "Status": {
                "Health": readings.cpu_health(),
                "State": "Enabled",
            }
        },
        "Processors": {
            "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/Processors"
        },
        "SKU": readings.get_sku(),
        "SerialNumber": readings.serial(),
        "SimpleStorage": {
            "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/SimpleStorage"
        },
        "Status": {
            "Health": readings.cpu_health(),  # Based on health functions (CPU, memory, etc.)
            "State": "Enabled"
        },
        "SystemType": readings.get_system_type(),
        "UUID": readings.system_uuid(),
        "Actions": {
            "#ComputerSystem.Reset": {
                "target": f"/redfish/v1/Systems/{readings.machine_id()}/Actions/ComputerSystem.Reset",
                "title": "Reset System",
                "ResetType@Redfish.AllowableValues": [
                    "On",
                    "ForceOff",
                    "GracefulShutdown",
                    "GracefulRestart",
                    "ForceRestart",
                    "PowerCycle"
                ]
            }
        }
    }

    return jsonify(computer_id)

logging.basicConfig(level=logging.INFO)

def reset_computer(system_id):
    """
    Executes the system reset action.

    Args:
        system_id (str): ID of the system to be reset.

    Returns:
        flask.Response: Success or error message.
    """
    data = request.json
    reset_type = data.get("ResetType", "GracefulRestart")

    allowable_resets = [
        "On", "ForceOff", "GracefulShutdown",
        "GracefulRestart", "ForceRestart", "PowerCycle"
    ]

    if reset_type not in allowable_resets:
        return jsonify({
            "error": "Invalid ResetType",
            "allowedValues": allowable_resets
        }), 400

    # Return response before executing command
    response = jsonify({
        "message": f"System {system_id} is being reset with {reset_type}"
    }), 200

    # Function to execute command asynchronously
    def execute_reset():
        try:
            if reset_type == "GracefulShutdown":
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
            elif reset_type == "ForceOff":
                subprocess.run(["sudo", "poweroff", "-f"], check=True)
            elif reset_type == "GracefulRestart":
                subprocess.run(["sudo", "shutdown", "-r", "now"], check=True)
            elif reset_type == "ForceRestart":
                subprocess.run(["sudo", "reboot", "-f"], check=True)
            elif reset_type == "PowerCycle":
                subprocess.run(["sudo", "poweroff", "-f"], check=True)
                subprocess.run(["sudo", "reboot", "-f"], check=True)
        except Exception as e:
            print(f"Error executing reset command: {str(e)}")

    # Executa o comando em uma nova thread
    threading.Thread(target=execute_reset).start()

    return response


def get_computersystem_id_ethernetInterfaces():
    """
    Returns the collection of Ethernet interfaces from the system.

    Returns:
        dict: Dictionary with Ethernet interfaces information in Redfish format.
    """
    eth = {
        "@odata.type": "#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "Name": "Ethernet Interface Collection",
        "Description": "System NICs on Raspberry Pi",
        "Members@odata.count": readings.eth_count(),
        "Members": readings.eth_members(), # Dictionary
        "Oem": {},
        "@odata.context": "/redfish/v1/$metadata#Systems/Members/" + readings.machine_id() + "/EthernetInterfaces/$entity",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/EthernetInterfaces",
    }
    return eth

def dynamic_eth_funcs():
    """
    Dynamically generates endpoint functions for each detected Ethernet interface.

    Returns:
        list: List of functions, each returning the Redfish dictionary of an interface.
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
                    "@odata.type": "#EthernetInterface.v1_0_2.EthernetInterface",
                    "Id": iface_name,
                    "Name": "Ethernet Interface",
                    "Description": "System NIC " + iface_number,
                    "Status": {
                        "State": stats['state'],
                    },
                    "FactoryMacAddress": stats['mac_address'],
                    "MacAddress": stats['mac_address'],
                    "SpeedMbps": stats['speed_mbps'],
                    "FullDuplex": stats['full_duplex'],
                    "IPv6DefaultGateway": stats['ipv6_gateway'],
                    "NameServers": stats['dns'],
                    "IPv4Addresses": stats['ipv4_addresses'],
                    "IPv6Addresses": stats['ipv6_addresses'],
                    "@odata.context": "/redfish/v1/$metadata#ComputerSystem/Members/" + readings.machine_id() + "/EthernetInterfaces/Members/$entity",
                    "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/EthernetInterfaces/" + iface_name,
                }
                return interface
            interface_function.__name__ = iface_name
            return interface_function

        systems_eth_endpoint_functions.append(bind_interface_function())
        interface_counter += 1
    return systems_eth_endpoint_functions

def get_systems_id_memory():
    """
    Returns the collection of memory modules from the system.

    Returns:
        dict: Dictionary with memory collection information in Redfish format.
    """
    mem = {
        "@odata.type": "#MemoryCollection.MemoryCollection",
        "Name": "Memory Module Collection",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Memory/1"
            }
        ],
        "@odata.context": "/redfish/v1/$metadata#MemoryCollection.MemoryCollection",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Memory"
    }
    return mem


def get_memory_info():
    """
    Executes lshw command to get detailed memory information.

    Returns:
        list: List of dictionaries with memory module information.
    """
    try:
        #  Executes lshw command and stores output
        result = subprocess.run(["sudo", "lshw", "-class", "memory", "-json"], 
                                capture_output=True, text=True, check=True)
        stdout_output = result.stdout.strip()  # Stores output to avoid repeated calls

        #  Checks if output is empty
        if not stdout_output:
            print(" ERROR: 'lshw' command returned empty output.")
            return []

        #  Attempts to load JSON, catching parsing errors
        try:
            memory_info = json.loads(stdout_output)
        except json.JSONDecodeError:
            print(f" ERROR: Failed to decode lshw JSON output.\nOutput: {stdout_output}")
            return []

        #  Step 1: Ensures memory_info is a list of dictionaries before calling .get()
        if isinstance(memory_info, list):
            memory_info = [dict(item) for item in memory_info if isinstance(item, dict)]  # Ensures they are dictionaries
            memory_info = [item for item in memory_info if str(item.get("id", "")).startswith("memory")]
        else:
            memory_info = []  # Ensures always returns a list

        return memory_info

    except subprocess.CalledProcessError as e:
        print(f" ERROR: Failed to execute 'lshw' command: {e}")
        return []
    except Exception as e:
        print(f" UNEXPECTED ERROR: {e}")
        return []


def get_memory_field(memory_info, field, default=None):
    """
    Gets a specific field from a memory module.

    Args:
        memory_info (list): List of memory dictionaries.
        field (str): Name of the field to obtain.
        default: Default value if field is not found.

    Returns:
        Field value or default value.
    """
    if isinstance(memory_info, list) and memory_info:
        for module in memory_info:
            if isinstance(module, dict) and field in module:
                value = module.get(field, default)
                # If field is 'capacity_mib', attempts conversion to int
                if field == "capacity_mib" and value is not None:
                    try:
                        return int(value)
                    except ValueError:
                        return default
                return value
    return default

def get_memory_type(description):
    """
    Maps memory description to valid Redfish type.

    Args:
        description (str): Description of memory type.

    Returns:
        str: Memory type in Redfish standard.
    """
    # Mapping to valid values
    valid_memory_types = {
        "DDR": "DRAM",
        "DDR2": "DRAM",
        "DDR3": "DRAM",
        "DDR4": "DRAM",
        "DDR5": "DRAM",
        "LPDDR4": "DRAM",
        "LPDDR5": "DRAM",
        "System memory": "DRAM",  # Maps 'System memory' to 'DRAM'
    }

    # Returns mapping or 'DRAM' as fallback
    return valid_memory_types.get(description, "DRAM")



def get_systems_id_memory_dimm():
    """
    Returns detailed information about the memory module.

    Returns:
        dict: Dictionary with memory module information in Redfish format.
    """
    memory_info = get_memory_info()  # Captures system memory data

    ram = {
        "@odata.type": "#Memory.v1_20_0.Memory",
        "@odata.context": "/redfish/v1/$metadata#Memory.Memory",
        "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/Memory/1",
        "Id": "1",
        "Name": "Slot 1",
        "Description": "Memory Module in Slot 1",
        
        # Mandatory fields with captured values
        "BusWidthBits": get_memory_field(memory_info, "bus width", default=64),  
        "DataWidthBits": get_memory_field(memory_info, "data width", default=64),  
        "DeviceLocator": get_memory_field(memory_info, "slot", default="DIMM Slot 1"),  
        "MemoryType": get_memory_type(get_memory_field(memory_info, "description", default="Unknown")),
        "CapacityMiB": readings.memory_total(),
        "RankCount": get_memory_field(memory_info, "rank", default=1),  

        # Status da memória (obrigatório)
        "Status": {
            "Health": readings.memory_health(),
            "State": "Enabled"
        }
    }
    return ram

def get_cpu_info_proc():
    """
    Gets CPU information from /proc/cpuinfo.

    Returns:
        tuple: (family, model) of CPU.
    """
    family, model = None, None
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "CPU part" in line:
                    model = line.split(":")[1].strip()
                elif "CPU revision" in line:
                    family = line.split(":")[1].strip()
    except Exception as e:
        print("Error getting CPU info via /proc/cpuinfo:", e)

    return family, model

family, model = get_cpu_info_proc()

def get_redfish_cpu_arch(arch):
    """
    Maps operating system architecture to corresponding Redfish value.

    Args:
        arch (str): Processor architecture (ex: 'armv7l', 'x86_64').

    Returns:
        str: Architecture in Redfish standard.
    """
    mapping = {
        "x86_64": "x86",
        "i386": "x86",
        "i686": "x86",
        "ia64": "IA-64",
        "armv7l": "ARM",  # 32-bit ARM
        "aarch64": "ARM",  # 64-bit ARM must be 'ARM'
        "mips": "MIPS",
        "mips64": "MIPS",
        "powerpc": "Power",
        "riscv32": "RISC-V",
        "riscv64": "RISC-V"
    }
    return mapping.get(arch, "OEM")  # If not found, set as 'OEM'

def get_redfish_instruction_set(arch):
    """
    Maps operating system architecture to corresponding Redfish instruction set.

    Args:
        arch (str): Processor architecture.

    Returns:
        str: Instruction set in Redfish standard.
    """
    mapping = {
        "x86_64": "x86-64",
        "i386": "x86",
        "i686": "x86",
        "ia64": "IA-64",
        "armv7l": "ARM-A32",  # 32-bit ARM
        "aarch64": "ARM-A64",  # 64-bit ARM should be 'ARM-A64'
        "mips": "MIPS32",
        "mips64": "MIPS64",
        "powerpc": "PowerISA",
        "riscv32": "RV32",
        "riscv64": "RV64"
    }
    return mapping.get(arch, "OEM")  # If not found, set as 'OEM'


def get_systems_id_processors():
    """
    Returns the collection of processors from the system.

    Returns:
        dict: Dictionary with processors information in Redfish format.
    """
    procs = {
        "@odata.type": "#ProcessorCollection.ProcessorCollection",
        "Name": "Processors Collection",
        "Members@odata.count": 1,
        "Members": [
            { 
                "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Processors/CPU1"
            }
        ],
        #"@odata.context": "/redfish/v1/$metadata#Systems/Links/Members/" + readings.machine_id() + "/Processors/#entity",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Processors",
    }
    return procs



def get_systems_id_processors_cpu1():
    """
    Returns detailed information about the main processor.

    Returns:
        dict: Dictionary with processor information in Redfish format.
    """
    cpu1 = {
        "@odata.type": "#Processor.v1_20_1.Processor",
        "@odata.context": "/redfish/v1/$metadata#Processor.Processor",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/Processors/CPU1",
        "Id": "CPU1",
        "Name": "Processor CPU1",
        "ProcessorType": "CPU",
        "ProcessorArchitecture": get_redfish_cpu_arch(readings.cpu_arch()),
        "InstructionSet": get_redfish_instruction_set(readings.cpu_arch()),
        "Manufacturer": readings.cpu_vendor(),
        "Model": readings.cpu_model(),
        "ProcessorId": {
            "EffectiveFamily": family if family else None,
            "EffectiveModel": model if model else None,
            "VendorId": readings.cpu_vendor() or None
        },
        "MaxSpeedMHz": int(readings.cpu_freq()) if readings.cpu_freq().isdigit() else 0,
        "TotalCores": int(readings.cpu_cores()) if readings.cpu_cores().isdigit() else 0,
        "TotalThreads": int(readings.cpu_threads()) if readings.cpu_threads().isdigit() else 0,
        "Status": {
            "Health": readings.cpu_health(),
        }
    }
    return cpu1


def get_systems_id_simpleStorage():
    """
    Returns the collection of simple storage devices from the system.

    Returns:
        dict: Dictionary with storage devices information in Redfish format.
    """
    storage = {
        "@odata.type": "#SimpleStorageCollection.SimpleStorageCollection",
        "Name": "Simple Storage Collection",
        "Members@odata.count": readings.storage_count(),
        "Members": readings.storage_members(),
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/SimpleStorage"
    }
    return storage

def dynamic_storage_funcs():
    """
    Dynamically generates endpoint functions for each detected storage device.

    Returns:
        list: List of functions, each returning the Redfish dictionary of a storage device.
    """
    systems_storage_endpoint_functions = []

    # Gets list of storage devices to avoid multiple API calls
    storage_names = readings.storage_names()

    for idx, member in enumerate(storage_names, start=1):  #  Uses enumerate() to correctly count devices

        def bind_storage_function(str_name=member, str_number=str(idx)):  #  Uses default arguments to capture values in correct scope

            def storage_function():
                stats = readings.storage_stats(str_name) or {}  #  Ensures stats is always a dictionary

                storage_device = {
                    "@odata.type": "#SimpleStorage.v1_3_2.SimpleStorage",
                    "Id": str_name,
                    "Name": stats.get('name', f"Storage {str_name}"),
                    "Description": stats.get('description', "Simple Storage Device"),
                    "Devices": [
                        {
                            "Name": stats.get('device_name', f"Device {str_number}"),
                            "Manufacturer": stats.get('manufacturer', "Unknown"),
                            "Model": stats.get('model', "Unknown"),
                            "CapacityBytes": int(stats['capacitybytes']) if isinstance(stats.get('capacitybytes'), str) and stats['capacitybytes'].isdigit() else stats.get('capacitybytes'),

                            "Status": {
                                "Health": stats.get('device_health', "OK"),  # Adding device Status
                                "State": stats.get('device_state', "Enabled"),
                            },
                        },
                    ],
                    "Status": {
                        "Health": stats.get('storage_health', "OK"),  # Status at SimpleStorage level
                        "State": stats.get('storage_state', "Enabled"),
                    },
                    "UefiDevicePath": stats.get('uefi_device_path', None),  # If not available, returns None
                    #"@odata.context": f"/redfish/v1/$metadata#ComputerSystem/Members/{readings.machine_id()}/SimpleStorage/Members/$entity",
                    "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/SimpleStorage/{str_name}"
                }
                
                return storage_device

            storage_function.__name__ = f"storage_{str_name}"  #  Ensures valid function name
            return storage_function

        systems_storage_endpoint_functions.append(bind_storage_function())

    return systems_storage_endpoint_functions