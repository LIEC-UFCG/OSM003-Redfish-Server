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
    machine_id = readings.machine_id()
    sensors = {
        "@odata.type": "#SensorCollection.SensorCollection",
        "Name": "Chassis Sensors",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": f"/redfish/v1/Chassis/{machine_id}/Sensors/CPUTemp"
            }
        ],
        "@odata.id": f"/redfish/v1/Chassis/{machine_id}/Sensors"
    }
    return sensors

def get_sensor(sensor_id):
    """
    Returns details for a single chassis sensor.

    Args:
        sensor_id (str): Sensor identifier.

    Returns:
        tuple: (dict, int) Sensor payload and HTTP status code.
    """
    machine_id = readings.machine_id()

    if sensor_id != "CPUTemp":
        return {"error": "Sensor not found"}, 404

    reading = readings.cpu_temp()
    state = "Enabled" if reading is not None else "UnavailableOffline"
    health = readings.temp_health()

    sensor_payload = {
        "@odata.type": "#Sensor.v1_6_0.Sensor",
        "Id": "CPUTemp",
        "Name": "CPU Temperature",
        "ReadingType": "Temperature",
        "ReadingUnits": "Cel",
        "Reading": reading,
        "PhysicalContext": "CPU",
        "Status": {
            "State": state,
            "Health": health
        },
        "@odata.id": f"/redfish/v1/Chassis/{machine_id}/Sensors/CPUTemp"
    }
    return sensor_payload, 200

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
    machine_id = readings.machine_id()
    reading = readings.cpu_temp()

    metrics = {
        "@odata.type": "#ThermalMetrics.v1_3_2.ThermalMetrics",
        "Id": "ThermalMetrics",
        "Name": "Chassis Thermal Metrics",
        "TemperatureReadingsCelsius": [
            {
                "Reading": reading,
                "DeviceName": "CPUSubsystem",
                "PhysicalContext": "CPU",
                "DataSourceUri": f"/redfish/v1/Chassis/{machine_id}/Sensors/CPUTemp"
            },
        ],
        "@odata.id": f"/redfish/v1/Chassis/{machine_id}/ThermalSubsystem/ThermalMetrics"
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
