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
    Retorna a coleção de sistemas computacionais.

    Returns:
        dict: Dicionário com informações da coleção de sistemas no formato Redfish.
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
    Retorna os detalhes do ComputerSystem no formato Redfish.

    Returns:
        flask.Response: Resposta JSON com os detalhes do ComputerSystem.
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
            "Count": 1,  # Raspberry Pi possui 1 processador físico
            "Model": readings.cpu_model(),  # Modelo do processador
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
            "Health": readings.cpu_health(),  # Baseado nas funções de saúde (CPU, memória, etc.)
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
    Executa a ação de Reset do sistema.

    Args:
        system_id (str): ID do sistema a ser resetado.

    Returns:
        flask.Response: Mensagem de sucesso ou erro.
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

    # Retornar a resposta antes de executar o comando
    response = jsonify({
        "message": f"System {system_id} is being reset with {reset_type}"
    }), 200

    # Função para executar o comando de forma assíncrona
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
            print(f"Erro ao executar o comando de reset: {str(e)}")

    # Executa o comando em uma nova thread
    threading.Thread(target=execute_reset).start()

    return response


def get_computersystem_id_ethernetInterfaces():
    """
    Retorna a coleção de interfaces Ethernet do sistema.

    Returns:
        dict: Dicionário com informações das interfaces Ethernet no formato Redfish.
    """
    eth = {
        "@odata.type": "#EthernetInterfaceCollection.EthernetInterfaceCollection",
        "Name": "Ethernet Interface Collection",
        "Description": "System NICs on Raspberry Pi",
        "Members@odata.count": readings.eth_count(),
        "Members": readings.eth_members(), # Dicionário
        "Oem": {},
        "@odata.context": "/redfish/v1/$metadata#Systems/Members/" + readings.machine_id() + "/EthernetInterfaces/$entity",
        "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/EthernetInterfaces",
    }
    return eth

def dynamic_eth_funcs():
    """
    Gera dinamicamente funções de endpoint para cada interface Ethernet detectada.

    Returns:
        list: Lista de funções, cada uma retornando o dicionário Redfish de uma interface.
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
    Retorna a coleção de módulos de memória do sistema.

    Returns:
        dict: Dicionário com informações da coleção de memória no formato Redfish.
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
    Executa o comando lshw para obter informações detalhadas da memória.

    Returns:
        list: Lista de dicionários com informações dos módulos de memória.
    """
    try:
        #  Executa o comando lshw e armazena a saída
        result = subprocess.run(["sudo", "lshw", "-class", "memory", "-json"], 
                                capture_output=True, text=True, check=True)
        stdout_output = result.stdout.strip()  # Armazena a saída para evitar chamadas repetidas

        #  Verifica se a saída está vazia
        if not stdout_output:
            print(" ERRO: O comando 'lshw' retornou uma saída vazia.")
            return []

        #  Tenta carregar o JSON, capturando erros de parsing
        try:
            memory_info = json.loads(stdout_output)
        except json.JSONDecodeError:
            print(f" ERRO: Falha ao decodificar a saída JSON do lshw.\nSaída: {stdout_output}")
            return []

        #  Passo 1: Garante que memory_info seja uma lista de dicionários antes de chamar .get()
        if isinstance(memory_info, list):
            memory_info = [dict(item) for item in memory_info if isinstance(item, dict)]  # Garante que são dicionários
            memory_info = [item for item in memory_info if str(item.get("id", "")).startswith("memory")]
        else:
            memory_info = []  # Garante que sempre retorna uma lista

        return memory_info

    except subprocess.CalledProcessError as e:
        print(f" ERRO: Falha ao executar o comando 'lshw': {e}")
        return []
    except Exception as e:
        print(f" ERRO INESPERADO: {e}")
        return []


def get_memory_field(memory_info, field, default=None):
    """
    Obtém um campo específico de um módulo de memória.

    Args:
        memory_info (list): Lista de dicionários de memória.
        field (str): Nome do campo a ser obtido.
        default: Valor padrão caso o campo não seja encontrado.

    Returns:
        Valor do campo ou valor padrão.
    """
    if isinstance(memory_info, list) and memory_info:
        for module in memory_info:
            if isinstance(module, dict) and field in module:
                value = module.get(field, default)
                # Se o campo for 'capacity_mib', tenta converter para int
                if field == "capacity_mib" and value is not None:
                    try:
                        return int(value)
                    except ValueError:
                        return default
                return value
    return default

def get_memory_type(description):
    """
    Mapeia a descrição da memória para o tipo Redfish válido.

    Args:
        description (str): Descrição do tipo de memória.

    Returns:
        str: Tipo de memória no padrão Redfish.
    """
    # Mapeamento para valores válidos
    valid_memory_types = {
        "DDR": "DRAM",
        "DDR2": "DRAM",
        "DDR3": "DRAM",
        "DDR4": "DRAM",
        "DDR5": "DRAM",
        "LPDDR4": "DRAM",
        "LPDDR5": "DRAM",
        "System memory": "DRAM",  # Mapeia 'System memory' para 'DRAM'
    }

    # Retorna o mapeamento ou 'DRAM' como fallback
    return valid_memory_types.get(description, "DRAM")



def get_systems_id_memory_dimm():
    """
    Retorna as informações detalhadas do módulo de memória.

    Returns:
        dict: Dicionário com informações do módulo de memória no formato Redfish.
    """
    memory_info = get_memory_info()  # Captura os dados da memória do sistema

    ram = {
        "@odata.type": "#Memory.v1_20_0.Memory",
        "@odata.context": "/redfish/v1/$metadata#Memory.Memory",
        "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/Memory/1",
        "Id": "1",
        "Name": "Slot 1",
        "Description": "Memory Module in Slot 1",
        
        # Campos obrigatórios com valores capturados
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
    Obtém informações da CPU a partir do /proc/cpuinfo.

    Returns:
        tuple: (family, model) da CPU.
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
        print("Erro ao obter CPU info via /proc/cpuinfo:", e)

    return family, model

family, model = get_cpu_info_proc()

def get_redfish_cpu_arch(arch):
    """
    Mapeia a arquitetura do SO para o valor Redfish correspondente.

    Args:
        arch (str): Arquitetura do processador (ex: 'armv7l', 'x86_64').

    Returns:
        str: Arquitetura no padrão Redfish.
    """
    mapping = {
        "x86_64": "x86",
        "i386": "x86",
        "i686": "x86",
        "ia64": "IA-64",
        "armv7l": "ARM",  # ARM de 32 bits
        "aarch64": "ARM",  # ARM de 64 bits tem que ser "ARM"
        "mips": "MIPS",
        "mips64": "MIPS",
        "powerpc": "Power",
        "riscv32": "RISC-V",
        "riscv64": "RISC-V"
    }
    return mapping.get(arch, "OEM")  # Se não encontrar, define como "OEM"

def get_redfish_instruction_set(arch):
    """
    Mapeia a arquitetura do SO para o conjunto de instruções Redfish correspondente.

    Args:
        arch (str): Arquitetura do processador.

    Returns:
        str: Conjunto de instruções no padrão Redfish.
    """
    mapping = {
        "x86_64": "x86-64",
        "i386": "x86",
        "i686": "x86",
        "ia64": "IA-64",
        "armv7l": "ARM-A32",  # ARM de 32 bits
        "aarch64": "ARM-A64",  # ARM de 64 bits deve ser "ARM-A64"
        "mips": "MIPS32",
        "mips64": "MIPS64",
        "powerpc": "PowerISA",
        "riscv32": "RV32",
        "riscv64": "RV64"
    }
    return mapping.get(arch, "OEM")  # Se não encontrar, define como "OEM"


def get_systems_id_processors():
    """
    Retorna a coleção de processadores do sistema.

    Returns:
        dict: Dicionário com informações dos processadores no formato Redfish.
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
    Retorna informações detalhadas do processador principal.

    Returns:
        dict: Dicionário com informações do processador no formato Redfish.
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
    Retorna a coleção de dispositivos de armazenamento simples do sistema.

    Returns:
        dict: Dicionário com informações dos dispositivos de armazenamento no formato Redfish.
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
    Gera dinamicamente funções de endpoint para cada dispositivo de armazenamento detectado.

    Returns:
        list: Lista de funções, cada uma retornando o dicionário Redfish de um dispositivo de armazenamento.
    """
    systems_storage_endpoint_functions = []

    # Obtém a lista de dispositivos de armazenamento para evitar múltiplas chamadas à API
    storage_names = readings.storage_names()

    for idx, member in enumerate(storage_names, start=1):  #  Usa enumerate() para contar corretamente os dispositivos

        def bind_storage_function(str_name=member, str_number=str(idx)):  #  Usa argumentos padrão para capturar valores no escopo correto

            def storage_function():
                stats = readings.storage_stats(str_name) or {}  #  Garante que stats seja sempre um dicionário

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
                                "Health": stats.get('device_health', "OK"),  # Adicionando Status do device
                                "State": stats.get('device_state', "Enabled"),
                            },
                        },
                    ],
                    "Status": {
                        "Health": stats.get('storage_health', "OK"),  # Status no nível do SimpleStorage
                        "State": stats.get('storage_state', "Enabled"),
                    },
                    "UefiDevicePath": stats.get('uefi_device_path', None),  # Se não disponível, retorna None
                    #"@odata.context": f"/redfish/v1/$metadata#ComputerSystem/Members/{readings.machine_id()}/SimpleStorage/Members/$entity",
                    "@odata.id": f"/redfish/v1/Systems/{readings.machine_id()}/SimpleStorage/{str_name}"
                }
                
                return storage_device

            storage_function.__name__ = f"storage_{str_name}"  #  Garante um nome de função válido
            return storage_function

        systems_storage_endpoint_functions.append(bind_storage_function())

    return systems_storage_endpoint_functions