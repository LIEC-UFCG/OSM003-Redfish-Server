from subprocess import check_output, Popen, call, DEVNULL, STDOUT, PIPE, CalledProcessError
from datetime import datetime
import psutil
import json
import os
import glob
import socket
import platform
import re
import subprocess
import config as app_config

def get_environment():
    """
    Detects the runtime environment.

    Returns:
        str: 'raspberry' when running on Raspberry Pi hardware, otherwise 'dcn'.
    """
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().lower()
            if "raspberry" in model:
                return "raspberry"
    except:
        pass

    return "dcn"


env = get_environment()

def serial():
    """
    Gets the serial number of the device.

    Returns:
        str: Device serial number.
    """
    if env == 'raspberry':
        return check_output(["cat", "/sys/firmware/devicetree/base/serial-number"]).decode("utf-8").replace('\u0000', '')

    elif env == 'dcn':
        try:
            path = "/sys/firmware/devicetree/base/serial-number"
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read().strip().replace('\u0000', '')
            return "Unknown"
        except Exception as e:
            print(f"Error getting serial: {e}")
            return "ERROR_SERIAL"


def machine_id():
    """
    Gets the Machine ID of the device.

    Executes 'hostnamectl' command and extracts the Machine ID from the output.

    Returns:
        str: Device Machine ID.
    """
    # Linux path: prefer hostnamectl output when available.
    try:
        hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
        machine_id_num = check_output(["grep", "Machine ID"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
        id_num = machine_id_num.split()[2]
        if id_num:
            return id_num
    except Exception:
        pass

    # Portable fallback: try /etc/machine-id.
    try:
        if os.path.exists('/etc/machine-id'):
            with open('/etc/machine-id', 'r', encoding='utf-8') as f:
                value = f.read().strip()
                if value:
                    return value
    except Exception:
        pass

    # Last-resort fallback for Windows/dev environments.
    return platform.node() or "UNKNOWN_MACHINE_ID"


def boot_id():
    """
    Gets the Boot ID of the Raspberry Pi.

    Returns:
        str: Device Boot ID.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    boot_id_num = check_output(["grep", "Boot ID"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    id_num = boot_id_num.split()[2]
    return id_num

def hostname():
    """
    Gets the hostname of the device.

    Returns:
        str: Device hostname.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    hostname = check_output(["grep", "Static hostname"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    name = hostname.split()[2]
    return name

def board_name():
    """
    Gets the board name of the device (abbreviated model).

    Returns:
        str: Abbreviated board name.
    """
    base_model = check_output(["cat", "/sys/firmware/devicetree/base/model"]).decode("utf-8").replace('\u0000', '')
    name = base_model.split()[:3]
    full_name = ""
    for i in name:
        full_name = full_name + i + " "
    full_name = full_name[:-1]
    return full_name

def model():
    """
    Gets the complete model of the device.

    Returns:
        str: Complete device model.
    """
    if env == 'raspberry':
        return check_output(["cat", "/sys/firmware/devicetree/base/model"]).decode("utf-8").replace('\u0000', '')
    
    elif env == 'dcn':
        try:
            path = "/sys/firmware/devicetree/base/model"
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read().strip().replace('\u0000', '')
        except Exception as e:
            print(f"Error reading {path}: {e}")

        # Trying to capture model from /proc/cpuinfo
        try:
            path = "/proc/cpuinfo"
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            return line.split(":")[1].strip()
        except Exception as e:
            print(f"Error reading {path}: {e}")

        return "Model not found"

def system_uuid():
    """
    Gets the system UUID from the root filesystem.

    Executes the 'lsblk' command to list block devices and extracts the UUID
    of the device mounted as '/' (system root).

    Returns:
        str or None: UUID do sistema de arquivos raiz, ou None em caso de erro.
    """
    try:
        # Executes lsblk and captures output
        lsblk_output = check_output(['lsblk', '-o', 'UUID,MOUNTPOINT']).decode("utf-8")
        # Iterates through each line of output
        for line in lsblk_output.splitlines()[1:]:  # Ignores header
            columns = line.split()  # Splits line into columns
            if len(columns) == 2 and columns[1] == '/':  # Checks if mounted as root
                uuid = columns[0]  # Assumes UUID is in first column
                return uuid
    except CalledProcessError as e:
        print(f"Error executing lsblk: {e}")
        return None  # or some default value

    return None


def power_led():
    """
    Returns the status of the device Power LED.

    Returns:
        str: "On" if LED is on, "Off" otherwise.
    """
    try:
        path = "/sys/class/leds/PWR/brightness"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                led_brightness = int(f.read().strip())
                return "On" if led_brightness > 0 else "Off"

        # Some systems expose the power LED under a different name.
        for fallback_path in (
            "/sys/class/leds/ACT/brightness",
            "/sys/class/leds/led1/brightness",
        ):
            if os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    led_brightness = int(f.read().strip())
                    return "On" if led_brightness > 0 else "Off"
    except Exception as e:
        print(f"Error reading power LED state: {e}")

    return "Off"



def manufacturer():
    """
    Gets the baseboard manufacturer.

    Returns:
        str: Manufacturer name, or 'Unknown' if unavailable.
    """
    env = get_environment()

    if env == 'raspberry':
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Revision"):
                        revision_code = line.strip().split(":")[1].strip().lower()
                        break
                else:
                    return "Unknown"

            rev_int = int(revision_code, 16)
            manufacturer_id = (rev_int >> 16) & 0xF

            manufacturers = {
                0: "Sony UK",
                1: "Egoman",
                2: "Embest",
                3: "Sony Japan",
                4: "Embest",
                5: "Stadium"
            }

            return manufacturers.get(manufacturer_id, "Unknown")

        except Exception as e:
            print(f"Error getting manufacturer on Raspberry Pi: {e}")
            return "Unknown"

    elif env == 'dcn':
        # Prefer sysfs sources because they are fast and do not require elevation.
        for path in (
            "/sys/devices/virtual/dmi/id/board_vendor",
            "/sys/devices/virtual/dmi/id/sys_vendor",
        ):
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        value = f.read().strip()
                        if value:
                            return value
            except Exception:
                continue

        # Fallback to dmidecode without sudo and with timeout to avoid HTTP hangs.
        try:
            result = subprocess.run(
                ['dmidecode', '-s', 'baseboard-manufacturer'],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            output = (result.stdout or "").strip()
            return output if output else "Unknown"
        except Exception as e:
            print(f"Error getting manufacturer on DCN: {e}")
            return "Unknown"

    else:
        return "Unknown"




def power_health():
    """
    Returns the power system health based on core and RAM voltage.

    Returns:
        str: "OK" if all voltages are within expected range, "Warning" otherwise.
    """
    if env == 'raspberry':
        core = check_output(['vcgencmd', 'measure_volts', 'core']).decode("utf-8").replace('\n', '')
        sdram_i = check_output(['vcgencmd', 'measure_volts', 'sdram_i']).decode("utf-8").replace('\n', '')
        sdram_c = check_output(['vcgencmd', 'measure_volts', 'sdram_c']).decode("utf-8").replace('\n', '')
        sdram_p = check_output(['vcgencmd', 'measure_volts', 'sdram_p']).decode("utf-8").replace('\n', '')
        volt_core = float(core.split('=')[1].replace('V', ''))
        volt_i = float(sdram_i.split('=')[1].replace('V', ''))
        volt_c = float(sdram_c.split('=')[1].replace('V', ''))
        volt_p = float(sdram_p.split('=')[1].replace('V', ''))
        if volt_core >= 1.2 and volt_core <= 1.3 and volt_i >= 1.2 and volt_i <= 1.3 and volt_c >= 1.2 and volt_c <= 1.3 and volt_p >= 1.2 and volt_p <= 1.3:
            return "OK"
        else:
            return "Warning"
    elif env == 'dcn':
        try:
            # Gets CPU and memory usage information to simulate system health
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Sets limits to determine health
            if cpu_usage < 80 and memory_usage < 80:  # Adjust values as needed
                return "OK"
            else:
                return "Warning"
        except Exception as e:
            print(f"Error calculating system health: {e}")
            return "Unknown"


def _safe_float(value):
    """Convert value to float when possible, else return None."""
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_number_from_file(path):
    """Read a numeric value from sysfs-style files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _safe_float(f.read().strip())
    except Exception:
        return None


def _to_watts(raw_value):
    """Normalize sysfs power values (uW/mW/W) into watts."""
    if raw_value is None:
        return None

    value = float(raw_value)

    if value >= 100000:
        # Common Linux power_supply unit: microwatts.
        return value / 1_000_000.0
    if value >= 1000:
        # Some platforms expose milliwatts.
        return value / 1000.0
    return value


def _is_supply_online(supply_dir):
    """Return True when power supply reports online, or if unknown."""
    online_value = _read_number_from_file(os.path.join(supply_dir, "online"))
    return online_value is None or int(online_value) == 1


def _get_supply_power_watts(candidates):
    """Try to read power from /sys/class/power_supply using candidate field names."""
    for supply_dir in glob.glob("/sys/class/power_supply/*"):
        if not _is_supply_online(supply_dir):
            continue

        for field in candidates:
            raw = _read_number_from_file(os.path.join(supply_dir, field))
            watts = _to_watts(raw)
            if watts is not None and watts > 0:
                return round(watts, 2)
    return None


def power_capacity_watts():
    """Return chassis power capacity in watts from device data or configuration."""
    measured = _get_supply_power_watts(["power_max", "power_max_design", "power_now"])
    if measured is not None:
        return measured

    configured = _safe_float(getattr(app_config, "POWER_CAPACITY_WATTS", None))
    return round(configured, 2) if configured is not None else 0.0


def power_allocated_watts():
    """Return allocated power in watts from device data or configuration."""
    measured = _get_supply_power_watts(["power_now", "power_avg"])
    if measured is not None:
        return measured

    configured = _safe_float(getattr(app_config, "POWER_ALLOCATED_WATTS", None))
    return round(configured, 2) if configured is not None else 0.0



def _get_dcn_thermal_temp():
    """
    Gets processor temperature from multiple sources in DCN (generic Linux).
    Tries thermal_zone, hwmon, and alternative sensors.

    Returns:
        float: Temperature in Celsius, or None if not found.
    """
    # Method 1: /sys/class/thermal/
    thermal_dir = "/sys/class/thermal"
    if os.path.exists(thermal_dir):
        # Tries thermal_zone0 first
        temp_path = os.path.join(thermal_dir, "thermal_zone0", "temp")
        if os.path.exists(temp_path):
            try:
                with open(temp_path, "r") as f:
                    temp_millicelsius = int(f.read().strip())
                    return temp_millicelsius / 1000.0
            except Exception:
                pass
        
        # Tries other thermal zones
        try:
            for zone_dir in sorted(os.listdir(thermal_dir)):
                if zone_dir.startswith("thermal_zone"):
                    temp_path = os.path.join(thermal_dir, zone_dir, "temp")
                    if os.path.exists(temp_path):
                        try:
                            with open(temp_path, "r") as f:
                                temp_millicelsius = int(f.read().strip())
                                return temp_millicelsius / 1000.0
                        except Exception:
                            continue
        except Exception:
            pass
    
    # Method 2: /sys/class/hwmon/
    hwmon_dir = "/sys/class/hwmon"
    if os.path.exists(hwmon_dir):
        try:
            for hwmon in sorted(os.listdir(hwmon_dir)):
                hwmon_path = os.path.join(hwmon_dir, hwmon)
                # Looks for temp*_input (temp1_input, temp2_input, etc)
                try:
                    for temp_file in sorted(os.listdir(hwmon_path)):
                        if temp_file.startswith("temp") and temp_file.endswith("_input"):
                            temp_input_path = os.path.join(hwmon_path, temp_file)
                            try:
                                with open(temp_input_path, "r") as f:
                                    temp_millicelsius = int(f.read().strip())
                                    # If the value is too small, it's probably not temperature
                                    if temp_millicelsius > 1000:  # At least 1°C
                                        return temp_millicelsius / 1000.0
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception:
            pass
    
    # Method 3: 'sensors' command if available
    try:
        output = check_output(["sensors"], stderr=DEVNULL).decode("utf-8")
        # Looks for lines with "Core" or "Package" and extracts temperature
        for line in output.split("\n"):
            if ("Core" in line or "Package" in line or "CPU" in line) and "°C" in line:
                # Extracts numeric value before °C
                parts = line.split()
                for i, part in enumerate(parts):
                    if "°C" in part and i > 0:
                        try:
                            temp_str = parts[i-1].replace("+", "").replace("°C", "")
                            return float(temp_str)
                        except Exception:
                            continue
    except Exception:
        pass
    
    return None


def temp_health():
    """
    Returns the status of the processor temperature.

    If temperature is greater than 95°C, returns "Warning", otherwise returns "OK".

    Returns:
        str: "OK", "Warning", or "Critical".
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_temp']).decode("utf-8").replace('\n', '')
        temp = float(vcgencmd.split('=')[1].replace("'C", ""))
        if temp <= 95:
            return "OK"
        else:
            return "Warning"
        
    elif env == 'dcn':
        try:
            temp = _get_dcn_thermal_temp()
            if temp is not None:
                if temp <= 95:
                    return "OK"
                else:
                    return "Warning"
            else:
                # Redfish Health must be one of: OK, Warning, Critical.
                # If temperature cannot be read, return a conservative value.
                return "Warning"
        except Exception as e:
            return "Warning"

    return "Warning"


def cpu_model():
    """
    Gets the CPU model string for the current environment.

    Returns:
        str: CPU model string, or an error/unknown message when not available.
    """
    env = get_environment()

    if env == 'raspberry':
        compatible_path = "/sys/firmware/devicetree/base/compatible"
        try:
            with open(compatible_path, "r") as f:
                compatible = f.read().strip()
            for item in compatible.split("\x00"):
                if "bcm" in item:
                    return item.split(",")[1]  # Example: bcm2711
            return "Model not found"
        except Exception as e:
            return f"Error reading model on Raspberry Pi: {e}"

    elif env == 'dcn':
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line.lower():
                        return line.split(":", 1)[1].strip()
            return "Model not found"
        except Exception as e:
            return f"Error reading model on DCN: {e}"

    else:
        return "Unknown environment"

def cpu_vendor():
    """
    Returns the processor vendor ID.

    Returns:
        str: Processor vendor ID.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    vendor = check_output(["grep", "Vendor ID"], stdin=lscpu.stdout).decode("utf-8")
    vendor_id = vendor.split()[2] 
    return vendor_id

def cpu_core_model():
    """
    Returns the processor core model.

    Returns:
        str: Core model including Vendor ID and Model name.
    """
    lscpu_a = Popen(['lscpu'], stdout=PIPE)
    vendor = check_output(["grep", "Vendor ID"], stdin=lscpu_a.stdout).decode("utf-8")
    vendor_id = vendor.split()[2]
    lscpu_b = Popen(['lscpu'], stdout=PIPE)
    model = check_output(["grep", "Model name"], stdin=lscpu_b.stdout).decode("utf-8")
    model_name = model.split()[2]
    return vendor_id + " " + model_name

def cpu_arch():
    """
    Returns the processor architecture.

    Returns:
        str: Processor architecture (ex: 'armv7l', 'aarch64', etc).
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    arch_number = check_output(["grep", "Architecture"], stdin=lscpu.stdout).decode("utf-8")
    arch = arch_number.split()[1]
    return arch

def cpu_byte_order():
    """
    Returns the processor byte order (endianness).

    Returns:
        str: Processor endianness (ex: 'Little Endian').
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    byte_order_out = check_output(["grep", "Byte Order"], stdin=lscpu.stdout).decode("utf-8")
    byte_order = byte_order_out.split()[2] + " " + byte_order_out.split()[3]
    return byte_order

def cpu_usage_percent():
    """
    Returns the current CPU usage percentage.

    Returns:
        float: CPU usage percentage.
    """
    return psutil.cpu_percent(interval=1)

def cpu_cores():
    """
    Returns the number of physical processor cores.

    Returns:
        str: Number of physical cores.
    """
    return str(psutil.cpu_count(logical=False))

def cpu_threads():
    """
    Returns the number of threads (logical cores) of the processor.

    Returns:
        str: Number of threads.
    """
    return str(psutil.cpu_count(logical=True))

def cpu_freq():
    """
    Returns the current processor operating frequency.

    Returns:
        str: Current frequency in MHz.
    """
    return str(psutil.cpu_freq()[0])

def cpu_min_freq():
    """
    Returns the minimum processor operating frequency.

    Returns:
        str: Minimum frequency in MHz.
    """
    return str(psutil.cpu_freq()[1]) + " MHz"

def cpu_max_freq():
    """
    Returns the maximum processor operating frequency.

    Returns:
        str: Maximum frequency in MHz.
    """
    return str(psutil.cpu_freq()[2]) + " MHz"

def cpu_cache_l1d():
    """
    Returns the processor L1d cache capacity.

    Returns:
        str: L1d cache capacity.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l1d = check_output(["grep", "L1d"], stdin=lscpu.stdout).decode("utf-8")
    cache_l1d = l1d.split()[2] + " " + l1d.split()[3]
    return cache_l1d

def cpu_cache_l1i():
    """
    Returns the processor L1i cache capacity.

    Returns:
        str: L1i cache capacity.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l1i = check_output(["grep", "L1i"], stdin=lscpu.stdout).decode("utf-8")
    cache_l1i = l1i.split()[2] + " " + l1i.split()[3]
    return cache_l1i

def cpu_cache_l2():
    """
    Returns the processor L2 cache capacity.

    Returns:
        str: L2 cache capacity.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l2 = check_output(["grep", "L2"], stdin=lscpu.stdout).decode("utf-8")
    cache_l2 = l2.split()[2] + " " + l2.split()[3]
    return cache_l2

def cpu_voltage():
    """
    Returns the processor supply voltage reading.

    Returns:
        str: Processor voltage.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'core']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        try:
            # Alternative paths where CPU voltage can be read
            voltage_paths = [
                "/sys/class/hwmon/hwmon0/in0_input",  # Typical path
                "/sys/class/hwmon/hwmon1/in0_input",  # Alternative path
                "/sys/class/hwmon/hwmon2/in0_input"   # Another possible path
            ]
            
            for voltage_path in voltage_paths:
                if os.path.exists(voltage_path):
                    with open(voltage_path, "r") as f:
                        # Usually, voltage is provided in millivolts (mV), so we convert to volts (V)
                        voltage = int(f.read().strip()) / 1000.0
                        return f"{voltage} V"
            
            # If none of the paths work
            #print("No voltage file found. Returning 'Unknown'.")
            return "Unknown"

        except Exception as e:
            # Exception handling
            print(f"Error getting CPU voltage: {e}")
            return "Unknown"

def cpu_health():
    """
    Returns processor health based on core voltage.

    Returns:
        str: "OK" if voltage is within expected range, "Warning" otherwise.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'core']).decode("utf-8").replace('\n', '')
        volt = float(vcgencmd.split('=')[1].replace('V', ''))
        if volt >= 1.2 and volt <= 1.3:
            return "OK"
        else:
            return "Warning"
    elif env == 'dcn':
        try:
            # Use substitute function to get voltage
            voltage = cpu_voltage()
            if voltage == "Unknown":
                # If voltage cannot be obtained, assign default Warning value
                return "Warning"

            # Convert voltage to number and evaluate
            voltage_value = float(voltage.split()[0])  # Removes the unit 'V'
            if 1.2 <= voltage_value <= 1.3:
                return "OK"
            elif 1.1 <= voltage_value < 1.2 or 1.3 < voltage_value <= 1.4:
                return "Warning"
            else:
                return "Critical"
        except Exception as e:
            print(f"Error determining CPU health: {e}")
            # Any error returns a conservative state
            return "Critical"

def cpu_temp():
    """
    Returns the processor temperature as a float.

    Returns:
        float | None: Processor temperature in Celsius, or None when unavailable.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_temp']).decode("utf-8").strip()
        temp = vcgencmd.split('=')[1].replace("'C", "")  # Removes "'C" from the end
        return float(temp)  # Convert to float and return
    
    elif env == 'dcn':
        try:
            temp = _get_dcn_thermal_temp()
            if temp is not None:
                return round(float(temp), 1)
            else:
                return None
        except Exception as e:
            return None

    return None

def memory_total():
    """
    Returns the total device memory in MiB as an integer.

    Returns:
        int: Total amount of memory in MiB. Returns 0 on error.
    """
    if env == 'raspberry':
        try:
            # Execute command to get total memory
            vcgencmd = Popen(['vcgencmd', 'get_config', 'int'], stdout=PIPE)
            total_mem = check_output(["grep", "total_mem"], stdin=vcgencmd.stdout).decode("utf-8").strip()
            
            # Extracts value after '=' and converts to integer
            mem = total_mem.split('=')[1]
            return int(mem)  # Ensures the returned value is an integer
        except (IndexError, ValueError, FileNotFoundError, CalledProcessError) as e:
            print(f"Error getting total memory: {e}")
            return 0  # Default value in case of error
    elif env == 'dcn':
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_kib = int(line.split()[1])  # Total memory in KiB
                        mem_gib = mem_kib / (1024 ** 2)  # Convert to GiB (1 GiB = 1024^2 KiB)
                        return round(mem_gib, 2)  # Returns rounded to 2 decimal places
            return None  # Returns None if total memory is not found
        except Exception as e:
            print(f"Error capturing total memory: {e}")
            return None



def memory_arm():
    """
    Returns the device memory allocated for general CPU use.

    Returns:
        str: Amount of memory allocated for the CPU.
    """
    if env == 'raspberry':
        mem_arm = check_output(["vcgencmd", "get_mem", "arm"]).decode("utf-8").replace('\n', '')
        mem = mem_arm.split('=')[1]
        return mem
    elif env == 'dcn':
        try:
            # Based on memory available to the system
            mem_info = psutil.virtual_memory()
            return f"{mem_info.available // (1024 ** 2)}M"  # Convert to MiB
        except Exception as e:
            print(f"Error capturing ARM memory: {e}")
            return "Unknown"


def memory_gpu():
    """
    Returns the device memory allocated for GPU.

    Returns:
        str: Amount of memory allocated for the GPU.
    """
    if env == 'raspberry':
        mem_gpu = check_output(["vcgencmd", "get_mem", "gpu"]).decode("utf-8").replace('\n', '')
        mem = mem_gpu.split('=')[1]
        return mem
    elif env == 'dcn':
        return "Unknown"


def memory_freq():
    """
    Returns the SDRAM memory clock speed.

    Returns:
        str: Memory frequency in MHz or 'Unknown' on error.
    """
    if env == 'raspberry':
        try:
            # Executes the vcgencmd command and captures the output
            vcgencmd = Popen(['vcgencmd', 'get_config', 'int'], stdout=PIPE)
            sdram_freq = check_output(["grep", "sdram_freq"], stdin=vcgencmd.stdout).decode("utf-8").strip()

            # Checks if the value was found
            if not sdram_freq:
                raise ValueError("sdram_freq not found in command output.")

            # Extracts the value after '='
            freq = sdram_freq.split('=')[1]
            return str(freq) + " MHz"
        except CalledProcessError:
            # In case grep doesn't find sdram_freq
            print("Error: 'sdram_freq' not found. Returning default value.")
            return "Unknown"
        except IndexError:
            # In case split can't access index [1]
            print("Error extracting 'sdram_freq' value.")
            return "Unknown"
    elif env == 'dcn':
        try:
            # Based on available hardware information on the system
            path = "/sys/class/dramfreq/dramfreq"
            if os.path.exists(path):
                with open(path, "r") as f:
                    freq_khz = int(f.read().strip())  # In kHz
                    freq_mhz = freq_khz // 1000  # Convert to MHz
                    return f"{freq_mhz} MHz"
            else:
                print(f"File {path} not found.")
                return "Unknown"
        except Exception as e:
            print(f"Error capturing memory frequency: {e}")
            return "Unknown"


def memory_used():
    """
    Returns the amount of memory used.

    Returns:
        str: Amount of memory used in MiB.
    """
    return str(int(psutil.virtual_memory()[3]/(2 ** 20)))

def memory_percent_used():
    """
    Returns the percentage of memory used.

    Returns:
        str: Percentage of memory used.
    """
    return str(psutil.virtual_memory()[2])

def memory_available():
    """
    Returns the amount of available memory.

    Returns:
        str: Amount of available memory in MiB.
    """
    return str(int(psutil.virtual_memory()[1]/(2 ** 20)))

def memory_free():
    """
    Returns the amount of free memory.

    Returns:
        str: Amount of free memory in MiB.
    """
    return str(int(psutil.virtual_memory()[4]/(2 ** 20)))

def memory_voltage():
    """
    Returns the SDRAM memory supply voltage reading.

    Returns:
        str: SDRAM memory voltage.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_i']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        try:
            path = "/sys/class/hwmon/hwmon0/in0_input"  # Replace with the correct path if available
            if os.path.exists(path):
                with open(path, "r") as f:
                    volt_mv = int(f.read().strip())  # In millivolts
                    volt_v = volt_mv / 1000  # Convert to volts
                    return f"{volt_v:.2f}V"
            else:
                print(f"File {path} not found.")
                return "Unknown"
        except Exception as e:
            print(f"Error capturing memory voltage: {e}")
            return "Unknown"


def memory_voltage_c():
    """
    Returns the SDRAM memory supply voltage reading (sdram_c).

    Returns:
        str: SDRAM memory voltage.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_c']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        return "Unknown"
    return "Unknown"

def memory_voltage_p():
    """
    Returns the SDRAM memory supply voltage reading (sdram_p).

    Returns:
        str: SDRAM memory voltage.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_p']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        return "Unknown"
    return "Unknown"

def memory_buffers():
    """
    Returns the amount of buffer memory.

    Returns:
        str: Amount of buffer memory in MiB.
    """
    return str(int(psutil.virtual_memory()[7]/(2 ** 20)))

def memory_cached():
    """
    Returns the amount of cached memory.

    Returns:
        str: Amount of cached memory in MiB.
    """
    return str(int(psutil.virtual_memory()[8]/(2 ** 20)))

def memory_health():
    """
    Returns memory health based on supply voltages.

    Returns:
        str: "OK" if all voltages are within expected range, "Warning" otherwise.
    """
    if env == 'raspberry':
        sdram_i = check_output(['vcgencmd', 'measure_volts', 'sdram_i']).decode("utf-8").replace('\n', '')
        sdram_c = check_output(['vcgencmd', 'measure_volts', 'sdram_c']).decode("utf-8").replace('\n', '')
        sdram_p = check_output(['vcgencmd', 'measure_volts', 'sdram_p']).decode("utf-8").replace('\n', '')
        volt_i = float(sdram_i.split('=')[1].replace('V', ''))
        volt_c = float(sdram_c.split('=')[1].replace('V', ''))
        volt_p = float(sdram_p.split('=')[1].replace('V', ''))
        if volt_i >= 1.2 and volt_i <= 1.3 and volt_c >= 1.2 and volt_c <= 1.3 and volt_p >= 1.2 and volt_p <= 1.3:
            return "OK"
        else:
            return "Warning"
    elif env == 'dcn':
        try:
            # Gets memory information with psutil
            mem = psutil.virtual_memory()
            percent_used = mem.percent  # Memory usage percentage

            # Sets the conditions to determine health status
            if percent_used < 80:  # If less than 80% of memory is being used
                return "OK"
            else:
                return "Warning"
        except Exception as e:
            print(f"Error calculating memory health: {e}")
            return "Unknown"


def swap_total():
    """
    Returns the total system swap memory.

    Returns:
        str: Total amount of swap memory in MiB.
    """
    return str(int(psutil.swap_memory()[0]/(2 ** 20)))

def swap_used():
    """
    Returns the swap memory currently in use.

    Returns:
        str: Amount of swap memory used in MiB.
    """
    return str(int(psutil.swap_memory()[1]/(2 ** 20)))

def swap_free():
    """
    Returns the free swap memory.

    Returns:
        str: Amount of free swap memory in MiB.
    """
    return str(int(psutil.swap_memory()[2]/(2 ** 20)))

def swap_percent():
    """
    Returns the swap memory usage percentage.

    Returns:
        str: Swap memory usage percentage.
    """
    return str(psutil.swap_memory()[3])

def os_name():
    """
    Returns the operating system name.

    Returns:
        str: Operating system name.
    """
    cat = Popen(['cat', '/etc/os-release'], stdout=PIPE)
    pretty_name = check_output(["grep", "PRETTY_NAME"], stdin=cat.stdout).decode("utf-8").replace('\n', '')
    name = pretty_name.split('=')[1].replace('"', '')
    return name

def os_version():
    """
    Returns the operating system version.

    Returns:
        str: Operating system version.
    """
    cat = Popen(['cat', '/etc/os-release'], stdout=PIPE)
    os_version = check_output(["grep", "VERSION_ID"], stdin=cat.stdout).decode("utf-8").replace('\n', '')
    version = os_version.split('=')[1].replace('"', '')
    return version

def os_kernel_version():
    """
    Returns the operating system kernel version.

    Returns:
        str: Kernel version.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    kernel_name = check_output(["grep", "Kernel"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    name = kernel_name.split()[1:]
    kernel = ""
    for word in name:
        if kernel == "":
            kernel = word
        else:
            kernel = kernel + " " + word
    return kernel

def eth_count():
    """
    Returns the number of network interfaces in the system.

    Returns:
        str: Number of detected network interfaces.
    """
    return str(len(psutil.net_if_addrs().keys()))

def eth_names():
    """
    Returns the names of network interfaces in the system.

    Returns:
        list: List with the names of network interfaces.
    """
    return list(psutil.net_if_addrs().keys())

def eth_members():
    """
    Returns the API endpoints for each network interface in the system.

    Returns:
        list: List of dictionaries with '@odata.id' field for each interface.
    """
    interface_names = psutil.net_if_addrs().keys()
    interfaces = []
    for name in interface_names:
        interfaces.append({
            "@odata.id": "/redfish/v1/Systems/" + machine_id() + "/EthernetInterfaces/" + name
        })
    return interfaces

def eth_stats(iface: str):
    """
    Returns statistics for a given network interface.

    Args:
        iface (str): Logical name of the network interface.

    Returns:
        dict: Interface statistics including MAC, speed, state, IP addresses, DNS, etc.
    """
    iface_addrs = psutil.net_if_addrs().get(iface, [])
    iface_stats = psutil.net_if_stats().get(iface, None)

    stats = {
        "mac_address": "00:00:00:00:00:00",
        "speed_mbps": 0,  # Ensures this value is an int
        "full_duplex": False,  # Ensures this value is a boolean
        "state": "Disabled",
        "link_status": "NoLink",  # Default value if not detected
        "ipv6_gateway": None,  # IPv6 gateway removed as it's not being used
        "dns": [],
        "ipv4_addresses": [],
        "ipv6_addresses": [],
        "IPv4StaticAddresses": []  # Stores gateway separately
    }

    # Collecting DNS servers
    nmcli1 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
    is_there_dns = call(["grep", "DNS"], stdin=nmcli1.stdout, stdout=DEVNULL, stderr=STDOUT)
    if is_there_dns == 0:
        nmcli1 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
        dns_parse = check_output(["grep", "DNS"], stdin=nmcli1.stdout).decode("utf-8")
        dns_break_lines = dns_parse.split('\n')[:-1]
        for line in dns_break_lines:
            stats['dns'].append(line.split()[1])

    # Getting interface information
    for snicaddr in iface_addrs:
        if snicaddr.family == 2:  # IPv4
            nmcli2 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
            gateway_parse = check_output(["grep", "IP4.GATEWAY"], stdin=nmcli2.stdout).decode("utf-8").replace('\n', '')
            gateway = gateway_parse.split()[1] if "IP4.GATEWAY" in gateway_parse else "0.0.0.0"

            # Checks if the gateway is a valid IP address
            if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", gateway):
                stats["IPv4StaticAddresses"].append({"Address": gateway})  # Keeps separate from IPv4Addresses

            stats['ipv4_addresses'].append({
                "Address": snicaddr.address,
                "SubnetMask": snicaddr.netmask,
                "AddressOrigin": "Static"
            })

        elif snicaddr.family == 10:  # IPv6
            prefix = bin(int(snicaddr.netmask.replace(':', ''), 16))
            prefix_length = len(str(prefix).replace('0', '').replace('b', ''))
            stats['ipv6_addresses'].append({
                "Address": snicaddr.address,
                "PrefixLength": prefix_length,
                "AddressOrigin": "Static",
                "AddressState": "Preferred"
            })

        elif snicaddr.family == 17:  # MAC Address
            stats['mac_address'] = snicaddr.address

    # Adjusting interface state
    if iface_stats and iface_stats.isup:
        stats['state'] = "Enabled"
        stats['link_status'] = "LinkUp"
    else:
        stats['state'] = "Disabled"
        stats['link_status'] = "NoLink"

    if iface_stats and iface_stats.duplex == 2:
        stats['full_duplex'] = True  # Convert to boolean

    stats['speed_mbps'] = iface_stats.speed if iface_stats and iface_stats.speed > 0 else 1000  # Default para 1Gbps

    return stats

def storage_count():
    """
    Returns the number of storage devices connected to the system.

    Returns:
        int: Number of detected storage devices.
    """
    return len(storage_names())

def storage_members():
    """
    Returns the API endpoint URLs for storage devices connected to the system.

    Returns:
        list: List of dictionaries with '@odata.id' field for each device.
    """
    disk_members = []
    for disk_name in storage_names():
        disk_members.append({
            "@odata.id": "/redfish/v1/Systems/" + machine_id() + "/SimpleStorage/" + disk_name
        })
    return disk_members

def storage_names():
    """
    Returns the logical names of connected storage devices.

    Returns:
        list: List with the names of storage devices.
    """
    disk_names = []
    try:
        lsblk_output = check_output(["lsblk", "-dn", "-o", "NAME,TYPE"], stderr=DEVNULL).decode("utf-8")
    except (FileNotFoundError, CalledProcessError, OSError):
        return disk_names

    for line in lsblk_output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "disk":
            disk_names.append(parts[0])
    return disk_names

def storage_stats(device):
    """
    Returns statistics for a given storage device.

    Args:
        device (str): Logical name of the device.

    Returns:
        dict: Dictionary with information such as name, description, manufacturer, model and capacity.
    """
    stats = {
        'name': "Unknown",
        'description': "Unknown",
        'device_name': "Unknown",
        'manufacturer': "Unknown",
        'model': "Unknown",
        'capacitybytes': "Unknown"
    }

    if env == 'raspberry':
        try:
            lshw = json.loads(subprocess.check_output([
                "sudo", "lshw", "-class", "disk", "-json"
            ]).decode("utf-8"))

            for entry in lshw:
                if entry.get('logicalname') == f"/dev/{device}":
                    stats['name'] = entry.get('logicalname', stats['name'])
                    stats['description'] = entry.get('description', stats['description'])
                    stats['device_name'] = entry.get('logicalname', stats['device_name'])
                    stats['manufacturer'] = entry.get('vendor', stats['manufacturer'])
                    stats['model'] = entry.get('product', stats['model'])
                    stats['capacitybytes'] = entry.get('size', stats['capacitybytes'])
                    break  # Found target device, can stop here

        except Exception as e:
            print(f"Error getting information via lshw: {e}")

    elif env == 'dcn':
        try:
            result = subprocess.check_output([
                'lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT', '-J'
            ]).decode("utf-8")

            devices = json.loads(result)

            for blk_device in devices['blockdevices']:
                if blk_device.get('name') == device:
                    stats['name'] = blk_device.get('name', stats['name'])
                    stats['description'] = blk_device.get('type', stats['description'])
                    stats['device_name'] = blk_device.get('name', stats['device_name'])
                    stats['model'] = blk_device.get('model', stats['model'])
                    stats['capacitybytes'] = blk_device.get('size', stats['capacitybytes'])
                    break  # Found target device, can stop here

        except Exception as e:
            print(f"Error getting information via lsblk: {e}")

    return stats


def session_count():
    """
    Returns the number of active sessions in the system.

    Returns:
        int: Number of currently active user sessions.
    """
    return len(psutil.users())

def session_members():
    """
    Returns endpoints relative to each active session.

    Returns:
        list: List of dictionaries with '@odata.id' field for each active session.
    """
    members = []
    for session in psutil.users():
        members.append({
            "@odata.id": "/redfish/v1/SessionService/" + session[0]
        })
    return members

def session_login_time(user):
    """
    Returns the login date and time for the specified user.

    Args:
        user (str): User name.

    Returns:
        str: Login date and time in ISO 8601 format, or "Unknown" if not found.
    """
    for session in psutil.users():
        if session[0] == user:
            return datetime.fromtimestamp(session[3]).isoformat()
    return "Unknown"

def process_counter():
    """
    Returns the number of processes allocated in the system.

    Returns:
        int: Number of running processes.
    """
    process_parse = check_output(["ps", "-eo", "pid,lstart,cmd"]).decode("utf-8")
    process = process_parse.split('\n')[1:-2]
    return len(process)

def process_pids():
    """
    Returns the list of PIDs of allocated processes.

    Returns:
        list: List of strings with process PIDs.
    """
    processes_parse = check_output(["ps", "-eo", "pid"]).decode("utf-8")
    processes = processes_parse.split('\n')[1:-2]
    pids = []
    for process in processes:
        pids.append(process.split()[0])
    return pids

def process_members():
    """
    Returns the endpoint URLs for each process.

    Returns:
        list: List of dictionaries with '@odata.id' and process name.
    """
    processes_parse = check_output(["ps", "-eo", "pid,lstart,cmd"]).decode("utf-8")
    processes = processes_parse.split('\n')[1:-2]
    members = []
    for process in processes:
        name = process.split()[6]
        members.append({"@odata.id": "/redfish/v1/TaskService/" + process.split()[0],
                        "Process Name": name})
    return members

def process_stats(pid):
    """
    Returns monitoring status for a specified process.

    Args:
        pid (str): Process PID.

    Returns:
        dict: Dictionary with process information (pid, start_time, name, status).
    """
    processes_parse = check_output(["ps", "-eo", "pid,lstart,s,cmd"]).decode("utf-8")
    processes = processes_parse.split('\n')[1:-2]
    for process in processes:
        proc_split = process.split()
        if(proc_split[0] == pid):
            date_info = proc_split[2] + " " + proc_split[3] + " " + proc_split[4] + " " + proc_split[5]
            date_fmt = "%b %d %H:%M:%S %Y"
            date_iso = datetime.strptime(date_info, date_fmt).isoformat()
            name_splits = proc_split[7:]
            name = ""
            for i in name_splits:
                name = name + i + " "
            name = name[:-1]
            stat = proc_split[6]
            status_text = "Unknown"

            if stat == 'D':
                status_text = "Uninterruptible sleep"
            elif stat == 'I':
                status_text = "Idle kernel thread"
            elif stat == 'R':
                status_text = "Running"
            elif stat == 'S':
                status_text = "Waiting"
            elif stat == 'T':
                status_text = "Stopped by job control signal"
            elif stat == 't':
                status_text = "Stopped by debugger"
            elif stat == 'W':
                status_text = "Paging"
            elif stat == 'X':
                status_text = "Dead"
            elif stat == 'Z':
                status_text = "Defunct process"

            proc_dict = {}
            proc_dict['pid'] = proc_split[0]
            proc_dict['start_time'] = date_iso
            proc_dict['name'] = name
            proc_dict['status'] = status_text
            return proc_dict
    return {'pid': '', 'start_time': '', 'name': '', 'status': ''}

####################################################################################

ASSET_TAG_FILE = "asset_tag.json"

def generate_asset_tag():   # MAKE WRITE
    """
    Generates an AssetTag based on the Raspberry Pi serial number.

    Returns:
        str: AssetTag in format 'RPI2-{SerialNumber}'. Returns 'RPI2-UNKNOWN' on error.
    """
    try:
        serial_number = serial().strip()  # Removes spaces or line breaks
        
        # Removes null characters (if still present)
        serial_number = serial_number.replace('\u0000', '')

        # Removes leading zeros
        serial_number_compact = serial_number.lstrip('0')

        # In case serial number is empty after adjustments
        if not serial_number_compact:
            serial_number_compact = "UNKNOWN"

        return f"RPI2-{serial_number_compact}"
    except Exception as e:
        print(f"Error generating AssetTag: {e}")
        return "RPI2-UNKNOWN"

_asset_tag = None  # Global variable to store the AssetTag

def load_asset_tag():
    """
    Loads the AssetTag from file. Generates a new one if the file doesn't exist or is corrupted.
    """
    global _asset_tag
    if os.path.exists(ASSET_TAG_FILE):  # Checks if the file exists
        try:
            with open(ASSET_TAG_FILE, "r") as f:    # Opens the file in read mode
                data = json.load(f)                 # Loads JSON from the file
                _asset_tag = data.get("AssetTag", generate_asset_tag())     # Uses existing value or generates a new one
        except Exception as e:
            print(f"Error loading AssetTag: {e}")
            _asset_tag = generate_asset_tag()               # Generates a value in case of error
    else:
        _asset_tag = generate_asset_tag()                   # Generates a new value if file doesn't exist

def save_asset_tag():
    """
    Saves the current AssetTag to file.
    """
    global _asset_tag
    try:
        with open(ASSET_TAG_FILE, "w") as f:        # Opens the file in write mode
            json.dump({"AssetTag": _asset_tag}, f)  # Saves the value in JSON format
    except Exception as e:
        print(f"Error saving AssetTag: {e}")    # Logs any error that occurred

def get_asset_tag():
    """
    Returns the AssetTag. Generates a new one if not yet defined.

    Returns:
        str: Current AssetTag.
    """
    global _asset_tag
    if _asset_tag is None:                      # Checks if the value hasn't been loaded yet
        _asset_tag = generate_asset_tag()       # Loads the value from file
    return _asset_tag                           # Returns the current AssetTag value

def set_asset_tag(new_tag):
    """
    Updates the AssetTag value and saves to file.

    Args:
        new_tag (str): New value for the AssetTag.
    """
    global _asset_tag
    _asset_tag = new_tag            # Updates the global variable with the new value
    save_asset_tag()                # Saves the new value to file



def get_chassis_type():
    """
    Determines the ChassisType of the Raspberry Pi.

    Returns:
        str: Physical type of the chassis, by default "StandAlone".
            - "StandAlone" for independent and self-sufficient devices
            - "Enclosure" for enclosures containing components or devices
            - "RackMount" for rack installation
            - "Blade" for blade servers
    """
    chassis_type = "StandAlone"  
    return chassis_type       


def get_sku():
    """
    Returns the SKU (Stock Keeping Unit) of the device.

    Returns:
        str: SKU code of the device. Fixed value, since it cannot be obtained automatically.
    """
    sku = "6914260"      # Try to get this value automatically using check_output
    return sku


def get_part_number():
    """
    Returns the part number (Part Number) of the device.

    Returns:
        str: Part number of the device. Fixed value, as it is not available directly in hardware.
    """
    part_number = "832-6274"    # Information provided in manufacturer specification. 
                                # Apparently, not available directly in hardware
    return part_number



def get_power():
    """
    Returns the power properties of the system.

    Returns:
        dict: Dictionary with information about power supplies and voltage sensors.
    """
    return {
        "PowerSupplies": [
            {
                "Voltage": cpu_voltage(),
                "Status": {
                    "Health": power_health(),
                }
            }
        ],
        "VoltageSensors": [
            {
                "Name": "CPU Voltage",
                "ReadingsVolts": cpu_voltage(),
                "Status": {
                    "Health": power_health(),
                }
            },
            {
                "Name": "Memory Voltage",
                "ReadingsVolts": memory_voltage(),
                "Status": {
                    "Health": memory_health(),
                }
            }
        ]
    }

def get_thermal():
    """
    Returns the thermal properties of the system.

    Returns:
        dict: Dictionary with information about system temperatures.
    """
    reading = cpu_temp()
    state = "Enabled" if reading is not None else "UnavailableOffline"
    return {
        "Temperatures": [
            {
                "Name": "CPU Temperature",
                "ReadingsCelsius": reading,
                "Status": {
                    "Health": temp_health(),
                    "State": state
                }
            }
        ],
    }

def get_system_type():
    """
    Returns the system type represented by the ComputerSystem resource.

    Returns:
        str: System type, default "Physical".
    """
    return "Physical"

# Default initial values
data_store = {
    "ServiceEnabled": True,
    "AccountLockoutCounterResetAfter": 30,
    "AccountLockoutCounterResetEnabled": True,
    "AccountLockoutDuration": 60,
    "AccountLockoutThreshold": 5
}

def get_account_service_data():
    """
    Returns the current AccountService data.

    Returns:
        dict: Dictionary with the current AccountService values.
    """
    return data_store

def update_account_service_data(new_data):
    """
    Updates AccountService data with information sent in PATCH request.

    Args:
        new_data (dict): Dictionary containing the keys and values to be updated.
    """
    for key, value in new_data.items():
        if key in data_store:
            data_store[key] = value

#-----------------------------------------------------------------------------------------------------------------------

SETTINGS_FILE = "event_service_settings.json"

def load_settings():
    """
    Loads event service settings from a JSON file.

    Returns:
        dict: Dictionary with loaded settings. Returns an empty dictionary on error or if the file doesn't exist.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configurations: {e}")
            return {}
    else:
        return {}

def save_settings(settings):
    """
    Saves event service settings to a JSON file.

    Args:
        settings (dict): Dictionary with the settings to be saved.
    """
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving configurations: {e}")

# Specific functions for DeliveryRetryAttempts
def get_delivery_retry_attempts():
    """
    Returns the number of retry attempts configured for events.

    Returns:
        int: Number of retry attempts. Default value is 3.
    """
    settings = load_settings()
    return settings.get("DeliveryRetryAttempts", 3)

def set_delivery_retry_attempts(value):
    """
    Updates the number of retry attempts for events.

    Args:
        value (int): New value for retry attempts.
    """
    settings = load_settings()
    settings["DeliveryRetryAttempts"] = value
    save_settings(settings)

# Specific functions for DeliveryRetryIntervalSeconds
def get_delivery_retry_interval_seconds():
    """
    Returns the interval (in seconds) between event delivery retry attempts.

    Returns:
        int: Interval in seconds. Default value is 5.
    """
    settings = load_settings()
    return settings.get("DeliveryRetryIntervalSeconds", 5)

def set_delivery_retry_interval_seconds(value):
    """
    Updates the interval between event delivery retry attempts.

    Args:
        value (int): New value for the interval in seconds.
    """
    settings = load_settings()
    settings["DeliveryRetryIntervalSeconds"] = value
    save_settings(settings)

# Specific functions for ServiceEnabled
def get_service_enabled():
    """
    Returns the status of the event service (enabled or not).

    Returns:
        bool: True if the service is enabled, False otherwise. Default value is True.
    """
    settings = load_settings()
    return settings.get("ServiceEnabled", True)

def set_service_enabled(value):
    """
    Updates the status of the event service.

    Args:
        value (bool): True to enable, False to disable.
    """
    settings = load_settings()
    settings["ServiceEnabled"] = value
    save_settings(settings)

#-----------------------------------------------------------------------------------------------------------------------

# Log file path
LOG_FILE = "log_entries.json"

def load_log_entries():
    """
    Loads log entries from a JSON file.

    Returns:
        list: List of dictionaries representing log entries.
              Returns an empty list if the file doesn't exist or is empty/corrupted.
    """
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"Error loading log entries: {e}")
        return []

def save_log_entries(entries):
    """
    Saves log entries to a JSON file.

    Args:
        entries (list): List of dictionaries representing log entries.
    """
    try:
        with open(LOG_FILE, "w") as file:
            json.dump(entries, file, indent=4)
    except Exception as e:
        print(f"Error saving log entries: {e}")

def create_log_entry(entry_type, severity, message, message_id=None, event_id=None, entry_code=None):
    """
    Creates a new log entry and saves it to file.

    Args:
        entry_type (str): Type of log entry (ex: 'Event', 'Alert').
        severity (str): Severity of the event (ex: 'OK', 'Warning', 'Critical').
        message (str): Descriptive message of the event.
        message_id (str, optional): Message identifier.
        event_id (str, optional): Event identifier.
        entry_code (str, optional): Entry code.

    Returns:
        dict: Dictionary representing the new log entry created.
    """
    entries = load_log_entries()
    new_entry = {
        "Created": datetime.utcnow().isoformat() + "Z",
        "EntryType": entry_type,
        "Severity": severity,
        "Message": message,
        "MessageId": message_id if message_id else "Unknown",
        "EventId": event_id if event_id else str(len(entries) + 1),
        "EntryCode": entry_code if entry_code else "N/A",
    }
    entries.append(new_entry)
    save_log_entries(entries)
    return new_entry

def clear_logs():
    """
    Clears all log entries from the JSON file.

    This function overwrites the log file with an empty list.
    """
    try:
        # Checks if the log file exists
        if os.path.exists(LOG_FILE):
            # Writes an empty list to the file to clear logs
            with open(LOG_FILE, 'w') as log_file:
                json.dump([], log_file)
            print("Logs successfully cleared!")
        else:
            print(f"File {LOG_FILE} not found, nothing to clean.")
    except Exception as e:
        print(f"Error clearing logs: {e}")


def get_max_records():
    """
    Returns the maximum number of supported log records.

    Returns:
        int: Maximum number of records.
    """
    return 1000  # Maximum number of supported records

def get_overwrite_policy():
    """
    Returns the log overwrite policy.

    Returns:
        str: Overwrite policy (ex: 'WrapsWhenFull').
    """
    return "WrapsWhenFull"  # Overwrite policy

#-----------------------------------------------------------------------------------------------------------------------

# CommandShell
def get_command_shell_service_enabled():
    """
    Returns whether the CommandShell service is enabled.

    Returns:
        bool: True if the service is enabled, False otherwise.
    """
    return True  # Default enabled

def set_command_shell_service_enabled(value):
    """
    Updates the CommandShell service status.

    Args:
        value (bool): True to enable, False to disable.
    """
    # Logic to update the configuration
    print(f"CommandShell ServiceEnabled updated to {value}")

def get_command_shell_max_sessions():
    """
    Returns the maximum number of concurrent sessions allowed for CommandShell.

    Returns:
        int: Maximum number of concurrent sessions.
    """
    return 5  # Maximum number of concurrent sessions

def get_command_shell_connect_types():
    """
    Returns the connection types supported by CommandShell.

    Returns:
        list: List of strings with the supported connection types.
    """
    return ["SSH", "Telnet"]  # Supported types


# Storage files
DATE_TIME_FILE = "datetime.json"
DATE_TIME_OFFSET_FILE = "datetime_offset.json"
SERVICE_ENABLED_FILE = "service_enabled.json"

# DateTime
def get_datetime():
    """
    Returns the current DateTime value.

    Returns:
        str: Current date and time in ISO 8601 format (UTC), or saved value from file if it exists.
    """
    try:
        if os.path.exists(DATE_TIME_FILE):
            with open(DATE_TIME_FILE, "r") as file:
                content = file.read().strip()
                if content:
                    data = json.loads(content)
                    return data.get("DateTime", datetime.utcnow().isoformat() + "Z")
                else:
                    print("File datetime.json is empty.")
        return datetime.utcnow().isoformat() + "Z"
    except Exception as e:
        print(f"Error loading DateTime: {e}")
        return datetime.utcnow().isoformat() + "Z"


def set_datetime(new_datetime):
    """
    Updates the DateTime value.

    Args:
        new_datetime (str): New date/time in ISO 8601 format.
    """
    if not new_datetime:
        print("Invalid DateTime, nothing was saved.")
        return
    try:
        with open(DATE_TIME_FILE, "w") as file:
            json.dump({"DateTime": new_datetime}, file)
            print(f"DateTime updated to {new_datetime}")
    except Exception as e:
        print(f"Error updating DateTime: {e}")


# DateTimeLocalOffset
def get_datetime_offset():
    """
    Returns the current DateTimeLocalOffset value.

    Returns:
        str: Saved local time offset, or '+00:00' as default.
    """
    try:
        if os.path.exists(DATE_TIME_OFFSET_FILE):
            with open(DATE_TIME_OFFSET_FILE, "r") as file:
                content = file.read().strip()
                if content:
                    data = json.loads(content)
                    return data.get("DateTimeLocalOffset", "+00:00")
                else:
                    print("File datetime_offset.json is empty.")
        return "+00:00"
    except Exception as e:
        print(f"Error loading DateTimeLocalOffset: {e}")
        return "+00:00"

def set_datetime_offset(offset):
    """
    Updates the local time offset.

    Args:
        offset (str): New local time offset (ex: '+00:00').
    """
    try:
        with open(DATE_TIME_OFFSET_FILE, "w") as file:
            json.dump({"DateTimeLocalOffset": offset}, file)
            print(f"DateTimeLocalOffset updated to {offset}")
    except Exception as e:
        print(f"Error updating DateTimeLocalOffset: {e}")


# ServiceEnabled
def get_service_enabled():
    """
    Returns the current ServiceEnabled status.

    Returns:
        bool: True if the service is enabled, False otherwise.
    """
    try:
        if os.path.exists(SERVICE_ENABLED_FILE):
            with open(SERVICE_ENABLED_FILE, "r") as file:
                data = json.load(file)
                return data.get("ServiceEnabled", True)  # Default True
        return True
    except Exception as e:
        print(f"Error loading ServiceEnabled: {e}")
        return True

def set_service_enabled(enabled):
    """
    Updates the ServiceEnabled status.

    Args:
        enabled (bool): True to enable, False to disable.
    """
    try:
        with open(SERVICE_ENABLED_FILE, "w") as file:
            json.dump({"ServiceEnabled": enabled}, file)
            print(f"ServiceEnabled updated to {enabled}")
    except Exception as e:
        print(f"Error updating ServiceEnabled: {e}")




#-----------------------------------------------------------------------------------------------------------------------

# Storage files
FQDN_FILE = "fqdn.json"
HTTPS_CONFIG_FILE = "https_config.json"

# FQDN
def get_fqdn():
    """
    Returns the Fully Qualified Domain Name (FQDN).

    If the file doesn't exist or is corrupted, returns the system FQDN obtained via socket.

    Returns:
        str: FQDN saved in file or the system FQDN.
    """
    try:
        # Checks if FQDN_FILE exists
        if os.path.exists(FQDN_FILE):
            with open(FQDN_FILE, "r") as file:
                data = json.load(file)  # Loads JSON from file
                return data.get("FQDN", socket.getfqdn())  # Returns the value or system FQDN
        else:
            # Returns system FQDN if file does not exist
            return socket.getfqdn()
    except json.JSONDecodeError as e:
        # Captures JSON format errors
        print(f"Error decoding FQDN file: {e}")
        return socket.getfqdn()
    except Exception as e:
        # Captures other generic errors
        print(f"Error loading FQDN: {e}")
        return socket.getfqdn()

def set_fqdn(fqdn):
    """
    Updates the FQDN.

    Args:
        fqdn (str): New Fully Qualified Domain Name to save.
    """
    try:
        with open(FQDN_FILE, "w") as file:
            json.dump({"FQDN": fqdn}, file)
            print(f"FQDN updated to {fqdn}")
    except Exception as e:
        print(f"Error updating FQDN: {e}")


# HTTPS.Port
def get_https_port():
    """
    Returns the HTTPS port.

    Returns:
        int: Configured HTTPS port. Default value is 443.
    """
    try:
        if os.path.exists(HTTPS_CONFIG_FILE):
            with open(HTTPS_CONFIG_FILE, "r") as file:
                data = json.load(file)
                return data.get("Port", 443)  # Default port 443
        return 443
    except Exception as e:
        print(f"Error loading HTTPS.Port: {e}")
        return 443

def set_https_port(port):
    """
    Updates the HTTPS port.

    Args:
        port (int): New HTTPS port to save.
    """
    try:
        config = {"Port": port, "ProtocolEnabled": get_https_protocol_enabled()}
        with open(HTTPS_CONFIG_FILE, "w") as file:
            json.dump(config, file)
            print(f"HTTPS.Port updated to {port}")
    except Exception as e:
        print(f"Error updating HTTPS.Port: {e}")


# HTTPS.ProtocolEnabled
def get_https_protocol_enabled():
    """
    Returns the HTTPS protocol status.

    Returns:
        bool: True if HTTPS protocol is enabled, False otherwise. Default True.
    """
    try:
        if os.path.exists(HTTPS_CONFIG_FILE):
            with open(HTTPS_CONFIG_FILE, "r") as file:
                data = json.load(file)
                return data.get("ProtocolEnabled", True)  # Default True
        return True
    except Exception as e:
        print(f"Error loading HTTPS.ProtocolEnabled: {e}")
        return True

def set_https_protocol_enabled(enabled):
    """
    Updates the HTTPS protocol status.

    Args:
        enabled (bool): True to enable, False to disable.
    """
    try:
        config = {"Port": get_https_port(), "ProtocolEnabled": enabled}
        with open(HTTPS_CONFIG_FILE, "w") as file:
            json.dump(config, file)
            print(f"HTTPS.ProtocolEnabled updated to {enabled}")
    except Exception as e:
        print(f"Error updating HTTPS.ProtocolEnabled: {e}")


#-----------------------------------------------------------------------------------------------------------------------


def get_hostname():
    """
    Returns the system hostname.

    Returns:
        str: System hostname.
    """
    return socket.gethostname()

def get_kernel_name():
    """
    Returns the operating system kernel name.

    Returns:
        str: Kernel name (ex: 'Linux').
    """
    return platform.system()

def get_kernel_release():
    """
    Returns the operating system kernel release.

    Returns:
        str: Kernel release (ex: '5.10.17-v7l+').
    """
    return platform.release()

def get_kernel_version():
    """
    Returns the detailed operating system kernel version.

    Returns:
        str: Detailed kernel version.
    """
    return platform.version()

def get_last_boot_time():
    """
    Returns the date and time of the last system boot.

    Returns:
        str: Date and time of last boot in ISO 8601 format.
    """
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    return boot_time.isoformat()

def get_metrics():
    """
    Returns basic system metrics.

    Returns:
        dict: Dictionary with CPU usage (%) and memory usage (GB).
    """
    return {
        "CPUUsage": f"{str(psutil.cpu_percent())}%",
        "MemoryUsage": f"{round(psutil.virtual_memory().used / (1024**3), 2)}GB"
    }

def get_processor_architecture():
    """
    Returns the processor architecture.

    Returns:
        str: Processor architecture (ex: 'armv7l', 'aarch64').
    """
    return platform.machine()

def get_operating_system_name():
    """
    Returns the full operating system name.

    Returns:
        str: Full operating system name.
    """
    return platform.platform()

#-----------------------------------------------------------------------------------------------------------------------

# Path to the file that will store the ServiceEnabled state
SERVICE_ENABLED_FILE = "operating_system_metrics_state.json"

# Default initial state
default_state = {
    "OperatingSystemMetrics": True,
    "EthernetInterfaceMetrics": True,
    "MemoryMetrics": True,
    "ProcessorMetrics": True,
    "VolumePartitionMetrics": True
}

def load_service_enabled_state():
    """
    Loads ServiceEnabled state from JSON file.

    Returns:
        dict: Dictionary with current metrics state (ex: which metrics are enabled).
              If the file doesn't exist or is corrupted, returns the default state.
    """
    if os.path.exists(SERVICE_ENABLED_FILE):
        try:
            with open(SERVICE_ENABLED_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            print("File corrupted. Recreating with default state.")
            save_service_enabled_state(default_state)
    # Returns default state if file doesn't exist or is corrupted
    return default_state.copy()

def save_service_enabled_state(state):
    """
    Saves ServiceEnabled state to JSON file.

    Args:
        state (dict): Dictionary with the metrics state to be saved.
    Raises:
        ValueError: If the dictionary contains invalid keys.
    """
    # Validates keys before saving
    valid_keys = default_state.keys()
    if not all(key in valid_keys for key in state.keys()):
        raise ValueError("The state contains invalid keys.")
    
    with open(SERVICE_ENABLED_FILE, "w") as file:
        json.dump(state, file)

# Load the current state on initialization
service_enabled_state = load_service_enabled_state()


def get_ethernet_metrics(service_enabled=True):
    """
    Captures mandatory metrics for Ethernet interfaces.

    Args:
        service_enabled (bool): Indicates if the service is enabled (default: True).

    Returns:
        dict or list: Dictionary {"ServiceEnabled": False} if disabled, 
                      or list of metrics per interface if enabled.
    """
    if not is_service_enabled("EthernetInterfaceMetrics"):
        return {"ServiceEnabled": False}

    metrics = []
    for nic, stats in psutil.net_io_counters(pernic=True).items():
        metrics.append({
            "InterfaceName": nic,
            "DroppedPackets": stats.dropin + stats.dropout,
            "RxBytesPerSecond": stats.bytes_recv,
            "RxErrors": stats.errin,
            "RxPacketsPerSecond": stats.packets_recv,
            "TxBytesPerSecond": stats.bytes_sent,
            "TxErrors": stats.errout,
            "TxPacketsPerSecond": stats.packets_sent,
            "ServiceEnabled": True,
            "LinkSpeed": 1000
        })
    return metrics

def get_memory_metrics(service_enabled=True):
    """
    Captures mandatory memory metrics.

    Args:
        service_enabled (bool): Indicates if the service is enabled (default: True).

    Returns:
        dict: Dictionary with memory metrics or {"ServiceEnabled": False} if disabled.
    """
    if not is_service_enabled("MemoryMetrics"):
        return {"ServiceEnabled": False}

    mem = psutil.virtual_memory()
    return {
        "BuffersBytes": mem.buffers,
        "CachedBytes": mem.cached,
        "HugepageSizeBytes": 0,
        "HugepagesFree": 0,
        "HugepagesTotal": 0,
        "MemAvailableBytes": mem.available,
        "MemFreeBytes": mem.free,
        "ServiceEnabled": True,
        "TotalMemoryBytes": mem.total
    }

def get_processor_metrics(service_enabled=True):
    """
    Captures mandatory processor metrics.

    Args:
        service_enabled (bool): Indicates if the service is enabled (default: True).

    Returns:
        dict: Dictionary with processor metrics.
    """
    cpu_usage = cpu_usage_percent()
    cpu_util_pct_idle = 100 - cpu_usage


    #Load generally reflects the concurrency level, i.e., how many processes are competing for CPU time.
    # Gets the system load averages
    load1, load5, load15 = psutil.getloadavg()
    cores = psutil.cpu_count(logical=True)
    # Calculates the percentages based on the cores
    cpu_load_pct_1m = (load1 / cores) * 100
    cpu_load_pct_5m = (load5 / cores) * 100
    cpu_load_pct_15m = (load15 / cores) * 100
    
    return {
        "CpuLoadPct1m": round(cpu_load_pct_1m, 2),
        "CpuLoadPct5m": round(cpu_load_pct_5m, 2),
        "CpuLoadPct15m": round(cpu_load_pct_15m, 2),
        "CpuUtilPctIdle": round(cpu_util_pct_idle, 2),
        "CpuUtilPctSystem": cpu_usage,
        "ServiceEnabled": True
    }



def get_volume_metrics(service_enabled=True):
    """
    Captures mandatory metrics for storage volumes.

    Args:
        service_enabled (bool): Indicates if the service is enabled (default: True).

    Returns:
        dict or list: Dictionary {"ServiceEnabled": False} if disabled,
                      or list of metrics per volume if enabled.
    """
    if not is_service_enabled("VolumePartitionMetrics"):
        return {"ServiceEnabled": False}
    
    metrics = []
    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)
        metrics.append({
            "CapacityBytes": usage.total,
            "DiskFreeBytes": usage.free,
            "DiskUsedBytes": usage.used,
            "ServiceEnabled": True
        })
    return metrics

def is_service_enabled(metric_name):
    """
    Checks if the service for a metric is enabled.

    Args:
        metric_name (str): Name of the metric (ex: 'MemoryMetrics').

    Returns:
        bool: True if the metric is enabled, False otherwise.
    """
    return service_enabled_state.get(metric_name, False)

def get_metrics_timestamp():
    """
    Returns the timestamp of the last metrics update.

    Returns:
        str: Current date and time in ISO 8601 format with 'Z' suffix (UTC).
    """
    return datetime.utcnow().isoformat() + "Z"

    

#-----------------------------------------------------------------------------------------------------------------------

SSDP_CONFIG_FILE = "ssdp_config.json"


def _load_ssdp_config():
    """Load persisted SSDP settings from disk.

    Returns:
        dict: SSDP configuration dictionary with ProtocolEnabled key.
    """
    if os.path.exists(SSDP_CONFIG_FILE):
        try:
            with open(SSDP_CONFIG_FILE, "r") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"ProtocolEnabled": True}


def _save_ssdp_config(enabled):
    """Persist SSDP enabled state to disk.

    Args:
        enabled (bool): Desired SSDP protocol enabled state.
    """
    try:
        with open(SSDP_CONFIG_FILE, "w") as file:
            json.dump({"ProtocolEnabled": bool(enabled)}, file)
    except Exception as e:
        print(f"Error updating SSDP.ProtocolEnabled: {e}")

def get_ssdp_enabled():
    """
    Returns whether SSDP discovery is enabled.

    Returns:
        bool: Current SSDP enabled state.
    """
    config = _load_ssdp_config()
    return bool(config.get("ProtocolEnabled", True))

def set_ssdp_enabled(value):
    """
    Updates SSDP enabled state.

    Args:
        value (bool): New SSDP state.
    """
    _save_ssdp_config(bool(value))
