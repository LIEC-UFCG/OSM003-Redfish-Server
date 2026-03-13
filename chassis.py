import readings

def get_chassis():
    """
    Retorna a coleção de chassis do sistema.

    Returns:
        dict: Dicionário com informações da coleção de chassis no formato Redfish.
    """
    chassis = {
        "@odata.type": "#ChassisCollection.ChassisCollection",
        "Name": "Chassis Collection",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id()
            }
        ],
        "@odata.id": "/redfish/v1/Chassis"
    }
    return chassis

def get_chassis_id():
    """
    Retorna informações detalhadas do chassi identificado pelo ID.

    Returns:
        dict: Dicionário com informações do chassi no formato Redfish.
    """
    chassis_id = {
        "@odata.type": "#Chassis.v1_26_0.Chassis",
        "Id": readings.machine_id(),
        "Name": "Computer System Chassis",
        "AssetTag": readings.get_asset_tag(),
        "ChassisType": readings.get_chassis_type(),
        "Links": {
            "ComputerSystems": [
                {
                    "@odata.id": "/redfish/v1/Systems/" + readings.machine_id()
                }
            ],

            "ManagedBy": [
                {
                    "@odata.id": "/redfish/v1/Managers/" + readings.machine_id()
                }
            ],
        },
        "ThermalSubsystem": {
            "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id() + "/ThermalSubsystem"
        },
        "Manufacturer": readings.manufacturer(),
        "Model": readings.model(),
        "PartNumber": readings.get_part_number(),
        "SKU": readings.get_sku(),
        "SerialNumber":readings.serial(),
        "Status": {
            "Health": readings.cpu_health(),
            "State": "Enabled"
        },
        "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id()
    }
    return chassis_id

def get_sensors():
    """
    Retorna informações dos sensores do chassi.

    Returns:
        dict: Dicionário com leituras dos sensores do chassi no formato Redfish.
    """
    sensors = {
        "@odata.type": "#SensorCollection.SensorCollection",
        "Name": "Chassis sensors",
        "CPU Temperature": readings.cpu_temp(),
        "CPU Voltage": readings.cpu_voltage(),
        "SDRAM_I Voltage": readings.memory_voltage(),
        "SDRAM_C Voltage": readings.memory_voltage_c(),
        "SDRAM_P Voltage": readings.memory_voltage_p(),
        "@odata.id": "/redfish/v1/Chassis/"+readings.machine_id()+"/Sensors"
    }
    return sensors

def get_thermalSubsystem():
    """
    Retorna informações do subsistema térmico do chassi.

    Returns:
        dict: Dicionário com informações do subsistema térmico no formato Redfish.
    """
    thermalsub = {
        "@odata.type": "#ThermalSubsystem.v1_3_3.ThermalSubsystem",
        "Id": "ThermalSubsystem",
        "Name": "Thermal Subsystem for Chassis",
        "PhysicalContext": "CPU",
        "ThermalMetrics": {
            "@odata.id": "/redfish/v1/Chassis/"+readings.machine_id()+"/ThermalSubsystem/ThermalMetrics"
        },
        "Status": {
            "State": "Enabled",
            "Health": readings.temp_health()
        },
        "@odata.id": "/redfish/v1/Chassis/" + readings.machine_id() + "/ThermalSubsystem"
    }
    return thermalsub

def get_thermalMetrics():
    """
    Retorna as métricas térmicas do chassi.

    Returns:
        dict: Dicionário com leituras de temperatura do chassi no formato Redfish.
    """
    metrics = {
        "@odata.type": "#ThermalMetrics.v1_3_2.ThermalMetrics",
        "Id": "ThermalMetrics",
        "Name": "Chassis Thermal Metrics",
        "TemperatureReadingsCelsius": [
            {
                "Reading": readings.cpu_temp(),
                "DeviceName": "CPUSubsystem",
                "DataSourceUri": "/redfish/v1/Chassis/"+readings.machine_id()+"/Sensors"
            },
        ],
        "@odata.id": "/redfish/v1/Chassis/"+readings.machine_id()+"/ThermalSubsystem/ThermalMetrics"
    }
    return metrics

def get_powerSubsystem():
    """
    Retorna informações do subsistema de energia do chassi.

    Returns:
        dict: Dicionário com informações do subsistema de energia no formato Redfish.
    """
    power = {
        "@odata.type": "#PowerSubsystem.v1_1_3.PowerSubsystem",
        "Id": "PowerSubsystem",
        "Name": "Power Subsystem for Chassis",
        "Core Voltage": readings.cpu_voltage(),
        "SDRAM_I Voltage": readings.memory_voltage(),
        "SDRAM_C Voltage": readings.memory_voltage_c(),
        "SDRAM_P Voltage": readings.memory_voltage_p(),
        "Status": {
            "Health": readings.power_health(),
        },
        "@odata.id": "/redfish/v1/Chassis/"+readings.machine_id()+"/PowerSubsystem"
    }
    return power
