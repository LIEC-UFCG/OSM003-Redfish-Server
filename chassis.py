import readings


def _resolve_system_id(system_id=None):
    """Return the requested system ID or fall back to the local machine ID."""
    return system_id or readings.machine_id()

def get_chassis(system_id=None):
    """
    Returns the system chassis collection.

    Returns:
        dict: Dictionary with chassis collection information in Redfish format.
    """
    resolved_system_id = _resolve_system_id(system_id)
    chassis = {
        "@odata.type": "#ChassisCollection.ChassisCollection",
        "Name": "Chassis Collection",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}"
            }
        ],
        "@odata.id": "/redfish/v1/Chassis"
    }
    return chassis

def get_chassis_id(system_id=None):
    """
    Returns detailed information about the chassis identified by ID.

    Returns:
        dict: Dictionary with chassis information in Redfish format.
    """
    resolved_system_id = _resolve_system_id(system_id)
    chassis_id = {
        "@odata.type": "#Chassis.v1_26_0.Chassis",
        "Id": resolved_system_id,
        "Name": "Computer System Chassis",
        "AssetTag": readings.get_asset_tag(),
        "LocationIndicatorActive": readings.power_led() == "On",
        "ChassisType": readings.get_chassis_type(),
        "Links": {
            "ComputerSystems": [
                {
                    "@odata.id": f"/redfish/v1/Systems/{resolved_system_id}"
                }
            ],

            "ManagedBy": [
                {
                    "@odata.id": f"/redfish/v1/Managers/{resolved_system_id}"
                }
            ],
        },
        "ThermalSubsystem": {
            "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/ThermalSubsystem"
        },
        "PowerSubsystem": {
            "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem"
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
        "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}"
    }
    return chassis_id

def get_sensors(system_id=None):
    """
    Returns information about chassis sensors.

    Returns:
        dict: Dictionary with readings from chassis sensors in Redfish format.
    """
    machine_id = _resolve_system_id(system_id)
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

def get_sensor(sensor_id, system_id=None):
    """
    Returns details for a single chassis sensor.

    Args:
        sensor_id (str): Sensor identifier.

    Returns:
        tuple: (dict, int) Sensor payload and HTTP status code.
    """
    machine_id = _resolve_system_id(system_id)

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

def get_thermalSubsystem(system_id=None):
    """
    Returns information about the chassis thermal subsystem.

    Returns:
        dict: Dictionary with thermal subsystem information in Redfish format.
    """
    resolved_system_id = _resolve_system_id(system_id)
    thermalsub = {
        "@odata.type": "#ThermalSubsystem.v1_3_3.ThermalSubsystem",
        "Id": "ThermalSubsystem",
        "Name": "Thermal Subsystem for Chassis",
        "ThermalMetrics": {
            "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/ThermalSubsystem/ThermalMetrics"
        },
        "Oem": {
            "OSM003": {
                "PhysicalContext": "CPU"
            }
        },
        "Status": {
            "State": "Enabled",
            "Health": readings.temp_health()
        },
        "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/ThermalSubsystem"
    }
    return thermalsub

def get_thermalMetrics(system_id=None):
    """
    Returns the thermal metrics for the chassis.

    Returns:
        dict: Dictionary with temperature readings from the chassis in Redfish format.
    """
    machine_id = _resolve_system_id(system_id)
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

def get_powerSubsystem(system_id=None):
    """
    Returns information about the chassis power subsystem.

    Returns:
        dict: Dictionary with power subsystem information in Redfish format.
    """
    resolved_system_id = _resolve_system_id(system_id)
    capacity_watts = max(0.0, float(readings.power_capacity_watts()))
    allocated_watts_raw = max(0.0, float(readings.power_allocated_watts()))
    allocated_watts = min(allocated_watts_raw, capacity_watts)

    power = {
        "@odata.type": "#PowerSubsystem.v1_1_3.PowerSubsystem",
        "Id": "PowerSubsystem",
        "Name": "Power Subsystem for Chassis",
        "Allocation": {
            "AllocatedWatts": allocated_watts
        },
        "CapacityWatts": capacity_watts,
        "PowerSupplies": {
            "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem/PowerSupplies"
        },
        "PowerSupplyRedundancy": [],
        "Status": {
            "Health": readings.power_health(),
            "State": "Enabled"
        },
        "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem"
    }
    return power


def get_power_supplies(system_id=None):
    """Return the collection of power supplies for the chassis power subsystem."""
    resolved_system_id = _resolve_system_id(system_id)
    collection = {
        "@odata.type": "#PowerSupplyCollection.PowerSupplyCollection",
        "Name": "Power Supply Collection",
        "Members@odata.count": 1,
        "Members": [
            {
                "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem/PowerSupplies/PSU1"
            }
        ],
        "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem/PowerSupplies"
    }
    return collection


def get_power_supply(system_id=None, psu_id="PSU1"):
    """Return a single power supply resource."""
    resolved_system_id = _resolve_system_id(system_id)

    if psu_id != "PSU1":
        return {"error": "Power supply not found"}, 404

    power_supply = {
        "@odata.type": "#PowerSupply.v1_5_1.PowerSupply",
        "Id": "PSU1",
        "Name": "Power Supply 1",
        "Manufacturer": readings.manufacturer(),
        "Model": readings.model(),
        "PowerCapacityWatts": readings.power_capacity_watts(),
        "InputNominalVoltageType": readings.input_nominal_voltage_type(),
        "Status": {
            "Health": readings.power_health(),
            "State": "Enabled"
        },
        "@odata.id": f"/redfish/v1/Chassis/{resolved_system_id}/PowerSubsystem/PowerSupplies/PSU1"
    }
    return power_supply
