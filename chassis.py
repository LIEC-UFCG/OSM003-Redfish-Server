import readings

def get_chassis():
    """
    Returns the system chassis collection.

    Returns:
        dict: Dictionary with chassis collection information in Redfish format.
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
    Returns detailed information about the chassis identified by ID.

    Returns:
        dict: Dictionary with chassis information in Redfish format.
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
    Returns information about chassis sensors.

    Returns:
        dict: Dictionary with readings from chassis sensors in Redfish format.
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
    Returns information about the chassis thermal subsystem.

    Returns:
        dict: Dictionary with thermal subsystem information in Redfish format.
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
    Returns the thermal metrics for the chassis.

    Returns:
        dict: Dictionary with temperature readings from the chassis in Redfish format.
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
    Returns information about the chassis power subsystem.

    Returns:
        dict: Dictionary with power subsystem information in Redfish format.
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
