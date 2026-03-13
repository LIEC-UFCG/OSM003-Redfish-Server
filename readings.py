from subprocess import check_output, Popen, call, DEVNULL, STDOUT, PIPE, CalledProcessError
from datetime import datetime
import psutil
import json
import os
import socket
import platform
import re
import subprocess

def get_environment():
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
    Obtém o número de série do dispositivo.

    Returns:
        str: Número de série do dispositivo.
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
            print(f"Erro ao obter serial: {e}")
            return "ERROR_SERIAL"


def machine_id():
    """
    Obtém o Machine ID do dispositivo.

    Executa o comando 'hostnamectl' e extrai o Machine ID da saída.

    Returns:
        str: Machine ID do dispositivo.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    machine_id_num = check_output(["grep", "Machine ID"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    id_num = machine_id_num.split()[2]
    return id_num


def boot_id():
    """
    Obtém o Boot ID do Raspberry Pi.

    Returns:
        str: Boot ID do dispositivo.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    boot_id_num = check_output(["grep", "Boot ID"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    id_num = boot_id_num.split()[2]
    return id_num

def hostname():
    """
    Obtém o hostname (nome do host) do dispositivo.

    Returns:
        str: Hostname do dispositivo.
    """
    hostnamectl = Popen(['hostnamectl'], stdout=PIPE)
    hostname = check_output(["grep", "Static hostname"], stdin=hostnamectl.stdout).decode("utf-8").replace('\n', '')
    name = hostname.split()[2]
    return name

def board_name():
    """
    Obtém o nome da placa do dispositivo (modelo resumido).

    Returns:
        str: Nome resumido da placa.
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
    Obtém o modelo completo do dispositivo.

    Returns:
        str: Modelo completo do dispositivo.
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
            print(f"Erro ao ler {path}: {e}")

        # Tentando capturar o modelo a partir de /proc/cpuinfo
        try:
            path = "/proc/cpuinfo"
            if os.path.exists(path):
                with open(path, "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            return line.split(":")[1].strip()
        except Exception as e:
            print(f"Erro ao ler {path}: {e}")

        return "Modelo não encontrado"

def system_uuid():
    """
    Obtém o UUID do sistema de arquivos raiz.

    Executa o comando 'lsblk' para listar os dispositivos de bloco e extrai o UUID
    do dispositivo que está montado como '/' (raiz do sistema).

    Returns:
        str or None: UUID do sistema de arquivos raiz, ou None em caso de erro.
    """
    try:
        # Executa lsblk e captura a saída
        lsblk_output = check_output(['lsblk', '-o', 'UUID,MOUNTPOINT']).decode("utf-8")
        # Percorre cada linha da saída
        for line in lsblk_output.splitlines()[1:]:  # Ignora o cabeçalho
            columns = line.split()  # Divide a linha em colunas
            if len(columns) == 2 and columns[1] == '/':  # Verifica se está montada como root
                uuid = columns[0]  # Assume que o UUID é a primeira coluna
                return uuid
    except CalledProcessError as e:
        print(f"Erro ao executar lsblk: {e}")
        return None  # ou algum valor padrão

    return None


def power_led():
    """
    Retorna o status do LED de Power do dispositivo.

    Returns:
        str: "On" se o LED estiver aceso, "Off" caso contrário.
    """
    led_brightness = int(check_output(["cat", "/sys/class/leds/PWR/brightness"]).decode("utf-8"))
    if(led_brightness > 0):
        return "On"
    else:
        return "Off"



def manufacturer():
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
            print(f"Erro ao obter fabricante na Raspberry Pi: {e}")
            return "Unknown"

    elif env == 'dcn':
        try:
            output = check_output(['sudo', 'dmidecode', '-s', 'baseboard-manufacturer']).decode("utf-8").strip()
            return output if output else "Unknown"
        except Exception as e:
            print(f"Erro ao obter fabricante no DCN: {e}")
            return "Unknown"

    else:
        return "Unknown"




def power_health():
    """
    Retorna a saúde do sistema de alimentação baseado na tensão dos cores e da memória RAM.

    Returns:
        str: "OK" se todas as tensões estiverem dentro do intervalo esperado, "Warning" caso contrário.
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
            # Obtem informações do uso da CPU e memória para simular a saúde do sistema
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Define limites para determinar saúde
            if cpu_usage < 80 and memory_usage < 80:  # Ajuste os valores conforme necessário
                return "OK"
            else:
                return "Warning"
        except Exception as e:
            print(f"Erro ao calcular a saúde do sistema: {e}")
            return "Unknown"



def temp_health():
    """
    Retorna o status da temperatura do processador.

    Se a temperatura for maior que 95°C, retorna "Warning", caso contrário retorna "OK".

    Returns:
        str: "OK" ou "Warning" dependendo da temperatura.
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
            # Lê a temperatura do processador do sistema
            temp_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp = int(f.read().strip()) / 1000.0  # A temperatura geralmente está em millicelsius
                    if temp <= 95:
                        return "OK"
                    else:
                        return "Warning"
            else:
                print(f"Arquivo {temp_path} não encontrado.")
                return "Unknown"
        except Exception as e:
            print(f"Erro ao calcular o status da temperatura: {e}")
            return "Unknown"


def cpu_model():
    env = get_environment()

    if env == 'raspberry':
        compatible_path = "/sys/firmware/devicetree/base/compatible"
        try:
            with open(compatible_path, "r") as f:
                compatible = f.read().strip()
            for item in compatible.split("\x00"):
                if "bcm" in item:
                    return item.split(",")[1]  # Exemplo: bcm2711
            return "Modelo não encontrado"
        except Exception as e:
            return f"Erro ao ler modelo na Raspberry Pi: {e}"

    elif env == 'dcn':
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line.lower():
                        return line.split(":", 1)[1].strip()
            return "Modelo não encontrado"
        except Exception as e:
            return f"Erro ao ler modelo no DCN: {e}"

    else:
        return "Ambiente desconhecido"

def cpu_vendor():
    """
    Retorna o fabricante (vendor) dos núcleos do processador.

    Returns:
        str: Identificador do fabricante (Vendor ID).
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    vendor = check_output(["grep", "Vendor ID"], stdin=lscpu.stdout).decode("utf-8")
    vendor_id = vendor.split()[2] 
    return vendor_id

def cpu_core_model():
    """
    Retorna o modelo dos núcleos do processador.

    Returns:
        str: Modelo dos núcleos, incluindo Vendor ID e Model name.
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
    Retorna a arquitetura do processador.

    Returns:
        str: Arquitetura do processador (ex: 'armv7l', 'aarch64', etc).
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    arch_number = check_output(["grep", "Architecture"], stdin=lscpu.stdout).decode("utf-8")
    arch = arch_number.split()[1]
    return arch

def cpu_byte_order():
    """
    Retorna o endianess (ordem dos bytes) do processador.

    Returns:
        str: Endianess do processador (ex: 'Little Endian').
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    byte_order_out = check_output(["grep", "Byte Order"], stdin=lscpu.stdout).decode("utf-8")
    byte_order = byte_order_out.split()[2] + " " + byte_order_out.split()[3]
    return byte_order

def cpu_usage_percent():
    """
    Retorna a porcentagem de uso atual do processador.

    Returns:
        float: Porcentagem de uso da CPU.
    """
    return psutil.cpu_percent(interval=1)

def cpu_cores():
    """
    Retorna a quantidade de núcleos físicos do processador.

    Returns:
        str: Número de núcleos físicos.
    """
    return str(psutil.cpu_count(logical=False))

def cpu_threads():
    """
    Retorna a quantidade de threads (núcleos lógicos) do processador.

    Returns:
        str: Número de threads.
    """
    return str(psutil.cpu_count(logical=True))

def cpu_freq():
    """
    Retorna a frequência de operação atual do processador.

    Returns:
        str: Frequência atual em MHz.
    """
    return str(psutil.cpu_freq()[0])

def cpu_min_freq():
    """
    Retorna a frequência mínima de operação do processador.

    Returns:
        str: Frequência mínima em MHz.
    """
    return str(psutil.cpu_freq()[1]) + " MHz"

def cpu_max_freq():
    """
    Retorna a frequência máxima de operação do processador.

    Returns:
        str: Frequência máxima em MHz.
    """
    return str(psutil.cpu_freq()[2]) + " MHz"

def cpu_cache_l1d():
    """
    Retorna a capacidade de memória cache L1d do processador.

    Returns:
        str: Capacidade da cache L1d.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l1d = check_output(["grep", "L1d"], stdin=lscpu.stdout).decode("utf-8")
    cache_l1d = l1d.split()[2] + " " + l1d.split()[3]
    return cache_l1d

def cpu_cache_l1i():
    """
    Retorna a capacidade de memória cache L1i do processador.

    Returns:
        str: Capacidade da cache L1i.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l1i = check_output(["grep", "L1i"], stdin=lscpu.stdout).decode("utf-8")
    cache_l1i = l1i.split()[2] + " " + l1i.split()[3]
    return cache_l1i

def cpu_cache_l2():
    """
    Retorna a capacidade de memória cache L2 do processador.

    Returns:
        str: Capacidade da cache L2.
    """
    lscpu = Popen(['lscpu'], stdout=PIPE)
    l2 = check_output(["grep", "L2"], stdin=lscpu.stdout).decode("utf-8")
    cache_l2 = l2.split()[2] + " " + l2.split()[3]
    return cache_l2

def cpu_voltage():
    """
    Retorna a tensão de alimentação lida pelo processador.

    Returns:
        str: Tensão do processador.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'core']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        try:
            # Caminhos alternativos onde a tensão da CPU pode ser lida
            voltage_paths = [
                "/sys/class/hwmon/hwmon0/in0_input",  # Caminho típico
                "/sys/class/hwmon/hwmon1/in0_input",  # Possível caminho alternativo
                "/sys/class/hwmon/hwmon2/in0_input"   # Outro possível caminho
            ]
            
            for voltage_path in voltage_paths:
                if os.path.exists(voltage_path):
                    with open(voltage_path, "r") as f:
                        # Geralmente, a tensão é fornecida em milivolts (mV), então convertemos para volts (V)
                        voltage = int(f.read().strip()) / 1000.0
                        return f"{voltage} V"
            
            # Se nenhum dos caminhos funcionar
            #print("Nenhum arquivo de tensão encontrado. Retornando 'Unknown'.")
            return "Unknown"

        except Exception as e:
            # Tratamento de exceções
            print(f"Erro ao obter a tensão da CPU: {e}")
            return "Unknown"

def cpu_health():
    """
    Retorna a saúde do processador baseado na tensão dos cores.

    Returns:
        str: "OK" se a tensão estiver dentro do intervalo esperado, "Warning" caso contrário.
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
            # Utilize a função substituta para obter a tensão
            voltage = cpu_voltage()
            if voltage == "Unknown":
                # Se a tensão não puder ser obtida, atribui um valor padrão de Warning
                return "Warning"

            # Converta a tensão para um número e avalie
            voltage_value = float(voltage.split()[0])  # Remove a unidade 'V'
            if 1.2 <= voltage_value <= 1.3:
                return "OK"
            elif 1.1 <= voltage_value < 1.2 or 1.3 < voltage_value <= 1.4:
                return "Warning"
            else:
                return "Critical"
        except Exception as e:
            print(f"Erro ao determinar a saúde da CPU: {e}")
            # Qualquer erro retorna um estado conservador
            return "Critical"

def cpu_temp():
    """
    Retorna a temperatura do processador como um número float.

    Returns:
        float: Temperatura do processador em graus Celsius.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_temp']).decode("utf-8").strip()
        temp = vcgencmd.split('=')[1].replace("'C", "")  # Remove "'C" do final
        return float(temp)  # Converte para float e retorna
    
    elif env == 'dcn':
        try:
            temp_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_path):
                with open(temp_path, "r") as f:
                    temp_millicelsius = int(f.read().strip())  # Em millicelsius
                    temp_celsius = temp_millicelsius / 1000.0  # Converte para Celsius
                    return f"{temp_celsius:.1f}"  # Retorna com uma casa decimal
            else:
                print(f"Arquivo {temp_path} não encontrado.")
                return "Unknown"
        except Exception as e:
            print(f"Erro ao capturar a temperatura da CPU: {e}")
            return "Unknown"

def memory_total():
    """
    Retorna a memória total do dispositivo em MiB como um inteiro.

    Returns:
        int: Quantidade total de memória em MiB. Retorna 0 em caso de erro.
    """
    if env == 'raspberry':
        try:
            # Executa o comando para obter a memória total
            vcgencmd = Popen(['vcgencmd', 'get_config', 'int'], stdout=PIPE)
            total_mem = check_output(["grep", "total_mem"], stdin=vcgencmd.stdout).decode("utf-8").strip()
            
            # Extrai o valor após o '=' e converte para inteiro
            mem = total_mem.split('=')[1]
            return int(mem)  # Garante que o valor retornado é um inteiro
        except (IndexError, ValueError, FileNotFoundError, CalledProcessError) as e:
            print(f"Erro ao obter a memória total: {e}")
            return 0  # Valor padrão em caso de erro
    elif env == 'dcn':
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_kib = int(line.split()[1])  # Memória total em KiB
                        mem_gib = mem_kib / (1024 ** 2)  # Converte para GiB (1 GiB = 1024^2 KiB)
                        return round(mem_gib, 2)  # Retorna arredondado a 2 casas decimais
            return None  # Retorna None caso a memória total não seja encontrada
        except Exception as e:
            print(f"Erro ao capturar a memória total: {e}")
            return None



def memory_arm():
    """
    Retorna a memória do dispositivo alocada para CPU geral.

    Returns:
        str: Quantidade de memória alocada para a CPU.
    """
    if env == 'raspberry':
        mem_arm = check_output(["vcgencmd", "get_mem", "arm"]).decode("utf-8").replace('\n', '')
        mem = mem_arm.split('=')[1]
        return mem
    elif env == 'dcn':
        try:
            # Baseado na memória disponível para o sistema
            mem_info = psutil.virtual_memory()
            return f"{mem_info.available // (1024 ** 2)}M"  # Converte para MiB
        except Exception as e:
            print(f"Erro ao capturar memória ARM: {e}")
            return "Unknown"


def memory_gpu():
    """
    Retorna a memória do dispositivo alocada para GPU.

    Returns:
        str: Quantidade de memória alocada para a GPU.
    """
    if env == 'raspberry':
        mem_gpu = check_output(["vcgencmd", "get_mem", "gpu"]).decode("utf-8").replace('\n', '')
        mem = mem_gpu.split('=')[1]
        return mem
    elif env == 'dcn':
        return "Unknown"


def memory_freq():
    """
    Retorna a velocidade de clock da memória SDRAM.

    Returns:
        str: Frequência da memória em MHz ou 'Unknown' em caso de erro.
    """
    if env == 'raspberry':
        try:
            # Executa o comando vcgencmd e captura a saída
            vcgencmd = Popen(['vcgencmd', 'get_config', 'int'], stdout=PIPE)
            sdram_freq = check_output(["grep", "sdram_freq"], stdin=vcgencmd.stdout).decode("utf-8").strip()

            # Verifica se o valor foi encontrado
            if not sdram_freq:
                raise ValueError("sdram_freq não encontrado na saída do comando.")

            # Extrai o valor após o '='
            freq = sdram_freq.split('=')[1]
            return str(freq) + " MHz"
        except CalledProcessError:
            # Caso o grep não encontre sdram_freq
            print("Erro: 'sdram_freq' não encontrado. Retornando valor padrão.")
            return "Unknown"
        except IndexError:
            # Caso o split não consiga acessar o índice [1]
            print("Erro ao extrair o valor de 'sdram_freq'.")
            return "Unknown"
    elif env == 'dcn':
        try:
            # Baseado em informações de hardware disponíveis no sistema
            path = "/sys/class/dramfreq/dramfreq"
            if os.path.exists(path):
                with open(path, "r") as f:
                    freq_khz = int(f.read().strip())  # Em kHz
                    freq_mhz = freq_khz // 1000  # Converte para MHz
                    return f"{freq_mhz} MHz"
            else:
                print(f"Arquivo {path} não encontrado.")
                return "Unknown"
        except Exception as e:
            print(f"Erro ao capturar frequência da memória: {e}")
            return "Unknown"


def memory_used():
    """
    Retorna a quantidade de memória utilizada.

    Returns:
        str: Quantidade de memória utilizada em MiB.
    """
    return str(int(psutil.virtual_memory()[3]/(2 ** 20)))

def memory_percent_used():
    """
    Retorna a porcentagem de memória utilizada.

    Returns:
        str: Porcentagem de memória utilizada.
    """
    return str(psutil.virtual_memory()[2])

def memory_available():
    """
    Retorna a quantidade de memória disponível.

    Returns:
        str: Quantidade de memória disponível em MiB.
    """
    return str(int(psutil.virtual_memory()[1]/(2 ** 20)))

def memory_free():
    """
    Retorna a quantidade de memória livre.

    Returns:
        str: Quantidade de memória livre em MiB.
    """
    return str(int(psutil.virtual_memory()[4]/(2 ** 20)))

def memory_voltage():
    """
    Retorna a tensão de alimentação lida pela memória SDRAM (sdram_i).

    Returns:
        str: Tensão da memória SDRAM.
    """
    if env == 'raspberry':
        vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_i']).decode("utf-8").replace('\n', '')
        volt = vcgencmd.split('=')[1]
        return volt
    elif env == 'dcn':
        try:
            path = "/sys/class/hwmon/hwmon0/in0_input"  # Substitua pelo caminho correto, se disponível
            if os.path.exists(path):
                with open(path, "r") as f:
                    volt_mv = int(f.read().strip())  # Em milivolts
                    volt_v = volt_mv / 1000  # Converte para volts
                    return f"{volt_v:.2f}V"
            else:
                print(f"Arquivo {path} não encontrado.")
                return "Unknown"
        except Exception as e:
            print(f"Erro ao capturar tensão da memória: {e}")
            return "Unknown"


def memory_voltage_c():
    """
    Retorna a tensão de alimentação lida pela memória SDRAM (sdram_c).

    Returns:
        str: Tensão da memória SDRAM.
    """
    vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_c']).decode("utf-8").replace('\n', '')
    volt = vcgencmd.split('=')[1]
    return volt

def memory_voltage_p():
    """
    Retorna a tensão de alimentação lida pela memória SDRAM (sdram_p).

    Returns:
        str: Tensão da memória SDRAM.
    """
    vcgencmd = check_output(['vcgencmd', 'measure_volts', 'sdram_p']).decode("utf-8").replace('\n', '')
    volt = vcgencmd.split('=')[1]
    return volt

def memory_buffers():
    """
    Retorna a quantidade de memória de buffers.

    Returns:
        str: Quantidade de memória de buffers em MiB.
    """
    return str(int(psutil.virtual_memory()[7]/(2 ** 20)))

def memory_cached():
    """
    Retorna a quantidade de memória em cache.

    Returns:
        str: Quantidade de memória em cache em MiB.
    """
    return str(int(psutil.virtual_memory()[8]/(2 ** 20)))

def memory_health():
    """
    Retorna a saúde da memória baseado nas tensões de alimentação.

    Returns:
        str: "OK" se todas as tensões estiverem dentro do intervalo esperado, "Warning" caso contrário.
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
            # Obtem informações da memória com psutil
            mem = psutil.virtual_memory()
            percent_used = mem.percent  # Percentual de memória utilizada

            # Define as condições para determinar a saúde
            if percent_used < 80:  # Se menos de 80% da memória estiver sendo usada
                return "OK"
            else:
                return "Warning"
        except Exception as e:
            print(f"Erro ao calcular a saúde da memória: {e}")
            return "Unknown"


def swap_total():
    """
    Retorna a memória de swap total do sistema.

    Returns:
        str: Quantidade total de memória de swap em MiB.
    """
    return str(int(psutil.swap_memory()[0]/(2 ** 20)))

def swap_used():
    """
    Retorna a memória de swap utilizada no momento.

    Returns:
        str: Quantidade de memória de swap utilizada em MiB.
    """
    return str(int(psutil.swap_memory()[1]/(2 ** 20)))

def swap_free():
    """
    Retorna a memória de swap livre no momento.

    Returns:
        str: Quantidade de memória de swap livre em MiB.
    """
    return str(int(psutil.swap_memory()[2]/(2 ** 20)))

def swap_percent():
    """
    Retorna a porcentagem de uso da memória de swap.

    Returns:
        str: Porcentagem de uso da memória de swap.
    """
    return str(psutil.swap_memory()[3])

def os_name():
    """
    Retorna o nome do sistema operacional.

    Returns:
        str: Nome do sistema operacional.
    """
    cat = Popen(['cat', '/etc/os-release'], stdout=PIPE)
    pretty_name = check_output(["grep", "PRETTY_NAME"], stdin=cat.stdout).decode("utf-8").replace('\n', '')
    name = pretty_name.split('=')[1].replace('"', '')
    return name

def os_version():
    """
    Retorna a versão do sistema operacional.

    Returns:
        str: Versão do sistema operacional.
    """
    cat = Popen(['cat', '/etc/os-release'], stdout=PIPE)
    os_version = check_output(["grep", "VERSION_ID"], stdin=cat.stdout).decode("utf-8").replace('\n', '')
    version = os_version.split('=')[1].replace('"', '')
    return version

def os_kernel_version():
    """
    Retorna a versão do Kernel do sistema operacional.

    Returns:
        str: Versão do Kernel.
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
    Retorna a quantidade de interfaces de rede do sistema.

    Returns:
        str: Número de interfaces de rede detectadas.
    """
    return str(len(psutil.net_if_addrs().keys()))

def eth_names():
    """
    Retorna o nome das interfaces de rede do sistema.

    Returns:
        list: Lista com os nomes das interfaces de rede.
    """
    return list(psutil.net_if_addrs().keys())

def eth_members():
    """
    Retorna os endpoints da API para cada interface de rede do sistema.

    Returns:
        list: Lista de dicionários com o campo '@odata.id' para cada interface.
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
    Retorna estatísticas de uma determinada interface de rede.

    Args:
        iface (str): Nome lógico da interface de rede.

    Returns:
        dict: Estatísticas da interface, incluindo MAC, velocidade, estado, endereços IP, DNS, etc.
    """
    iface_addrs = psutil.net_if_addrs().get(iface, [])
    iface_stats = psutil.net_if_stats().get(iface, None)

    stats = {
        "mac_address": "00:00:00:00:00:00",
        "speed_mbps": 0,  # Garantindo que seja int
        "full_duplex": False,  # Garantindo que seja booleano
        "state": "Disabled",
        "link_status": "NoLink",  # Valor padrão caso não seja detectado
        "ipv6_gateway": None,  # IPv6 gateway removido pois não está sendo usado
        "dns": [],
        "ipv4_addresses": [],
        "ipv6_addresses": [],
        "IPv4StaticAddresses": []  # Para armazenar gateway separado
    }

    # Coletando servidores DNS
    nmcli1 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
    is_there_dns = call(["grep", "DNS"], stdin=nmcli1.stdout, stdout=DEVNULL, stderr=STDOUT)
    if is_there_dns == 0:
        nmcli1 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
        dns_parse = check_output(["grep", "DNS"], stdin=nmcli1.stdout).decode("utf-8")
        dns_break_lines = dns_parse.split('\n')[:-1]
        for line in dns_break_lines:
            stats['dns'].append(line.split()[1])

    # Pegando informações das interfaces
    for snicaddr in iface_addrs:
        if snicaddr.family == 2:  # IPv4
            nmcli2 = Popen(['nmcli', 'dev', 'show', iface], stdout=PIPE)
            gateway_parse = check_output(["grep", "IP4.GATEWAY"], stdin=nmcli2.stdout).decode("utf-8").replace('\n', '')
            gateway = gateway_parse.split()[1] if "IP4.GATEWAY" in gateway_parse else "0.0.0.0"

            # Verifica se o gateway é um IP válido
            if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", gateway):
                stats["IPv4StaticAddresses"].append({"Address": gateway})  # Mantém separado do IPv4Addresses

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

    # Ajustando estado da interface
    if iface_stats and iface_stats.isup:
        stats['state'] = "Enabled"
        stats['link_status'] = "LinkUp"
    else:
        stats['state'] = "Disabled"
        stats['link_status'] = "NoLink"

    if iface_stats and iface_stats.duplex == 2:
        stats['full_duplex'] = True  # Converte para booleano

    stats['speed_mbps'] = iface_stats.speed if iface_stats and iface_stats.speed > 0 else 1000  # Default para 1Gbps

    return stats

def storage_count():
    """
    Retorna a quantidade de dispositivos de armazenamento conectados ao sistema.

    Returns:
        int: Número de dispositivos de armazenamento detectados.
    """
    lsblk = Popen(['lsblk'], stdout=PIPE)
    disk_parse = check_output(["grep", "disk"], stdin=lsblk.stdout).decode("utf-8")
    disks = disk_parse.split('\n')[:-1]
    return len(disks)

def storage_members():
    """
    Retorna as URLs dos endpoints da API para dispositivos de armazenamento conectados.

    Returns:
        list: Lista de dicionários com o campo '@odata.id' para cada dispositivo.
    """
    lsblk = Popen(['lsblk'], stdout=PIPE)
    disk_parse = check_output(["grep", "disk"], stdin=lsblk.stdout).decode("utf-8")
    disks = disk_parse.split('\n')[:-1]
    disk_members = []
    for disk in disks:
        disk_name = disk.split()[0]
        disk_members.append({
            "@odata.id": "/redfish/v1/Systems/" + machine_id() + "/SimpleStorage/" + disk_name
        })
    return disk_members

def storage_names():
    """
    Retorna os nomes lógicos dos dispositivos de armazenamento conectados.

    Returns:
        list: Lista com os nomes dos dispositivos de armazenamento.
    """
    lsblk = Popen(['lsblk'], stdout=PIPE)
    disk_parse = check_output(["grep", "disk"], stdin=lsblk.stdout).decode("utf-8")
    disks = disk_parse.split('\n')[:-1]
    disk_names = []
    for disk in disks:
        disk_name = disk.split()[0]
        disk_names.append(disk_name)
    return disk_names

def storage_stats(device):
    """
    Retorna estatísticas de um determinado dispositivo de armazenamento.

    Args:
        device (str): Nome lógico do dispositivo.

    Returns:
        dict: Dicionário com informações como nome, descrição, fabricante, modelo e capacidade.
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
                    break  # Encontrou, pode parar

        except Exception as e:
            print(f"Erro ao obter informações via lshw: {e}")

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
                    break  # Encontrou, pode parar

        except Exception as e:
            print(f"Erro ao obter informações via lsblk: {e}")

    return stats


def session_count():
    """
    Retorna a quantidade de sessões ativas no sistema.

    Returns:
        int: Número de sessões de usuários atualmente ativas.
    """
    return len(psutil.users())

def session_members():
    """
    Retorna os endpoints relativos a cada sessão ativa.

    Returns:
        list: Lista de dicionários com o campo '@odata.id' para cada sessão ativa.
    """
    members = []
    for session in psutil.users():
        members.append({
            "@odata.id": "/redfish/v1/SessionService/" + session[0]
        })
    return members

def session_login_time(user):
    """
    Retorna a data e hora de login do usuário especificado.

    Args:
        user (str): Nome do usuário.

    Returns:
        str: Data e hora do login no formato ISO 8601, ou "Unknown" se não encontrado.
    """
    for session in psutil.users():
        if session[0] == user:
            return datetime.fromtimestamp(session[3]).isoformat()
    return "Unknown"

def process_counter():
    """
    Retorna a quantidade de processos alocados no sistema.

    Returns:
        int: Número de processos em execução.
    """
    process_parse = check_output(["ps", "-eo", "pid,lstart,cmd"]).decode("utf-8")
    process = process_parse.split('\n')[1:-2]
    return len(process)

def process_pids():
    """
    Retorna a lista de PIDs dos processos alocados.

    Returns:
        list: Lista de strings com os PIDs dos processos.
    """
    processes_parse = check_output(["ps", "-eo", "pid"]).decode("utf-8")
    processes = processes_parse.split('\n')[1:-2]
    pids = []
    for process in processes:
        pids.append(process.split()[0])
    return pids

def process_members():
    """
    Retorna as URLs dos endpoints referentes a cada processo.

    Returns:
        list: Lista de dicionários com '@odata.id' e nome do processo.
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
    Retorna status de monitoramento de um processo especificado.

    Args:
        pid (str): PID do processo.

    Returns:
        dict: Dicionário com informações do processo (pid, start_time, name, status).
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

def generate_asset_tag():   # FAZER ESCRITA
    """
    Gera um AssetTag baseado no número de série da Raspberry Pi.

    Returns:
        str: AssetTag no formato 'RPI2-{SerialNumber}'. Retorna 'RPI2-UNKNOWN' em caso de erro.
    """
    try:
        serial_number = serial().strip()  # Remove espaços ou quebras de linha
        
        # Remove caracteres nulos (se ainda houver)
        serial_number = serial_number.replace('\u0000', '')

        # Remove zeros à esquerda
        serial_number_compact = serial_number.lstrip('0')

        # Caso o número de série seja vazio após os ajustes
        if not serial_number_compact:
            serial_number_compact = "UNKNOWN"

        return f"RPI2-{serial_number_compact}"
    except Exception as e:
        print(f"Erro ao gerar AssetTag: {e}")
        return "RPI2-UNKNOWN"

_asset_tag = None  # Variável global para armazenar o AssetTag

def load_asset_tag():
    """
    Carrega o AssetTag do arquivo. Gera um novo se o arquivo não existir ou estiver corrompido.
    """
    global _asset_tag
    if os.path.exists(ASSET_TAG_FILE):  # Verifica se o arquivo existe
        try:
            with open(ASSET_TAG_FILE, "r") as f:    # Abre o arquivo em modo leitura
                data = json.load(f)                 # Carrega o JSON do arquivo
                _asset_tag = data.get("AssetTag", generate_asset_tag())     # Usa o valor ou gera um novo
        except Exception as e:
            print(f"Erro ao carregar o AssetTag: {e}")
            _asset_tag = generate_asset_tag()               # Gera um valor em caso de erro
    else:
        _asset_tag = generate_asset_tag()                   # Gera um novo valor se o arquivo não existir

def save_asset_tag():
    """
    Salva o AssetTag atual no arquivo.
    """
    global _asset_tag
    try:
        with open(ASSET_TAG_FILE, "w") as f:        # Abre o arquivo em modo escrita
            json.dump({"AssetTag": _asset_tag}, f)  # Salva o valor em formato JSON
    except Exception as e:
        print(f"Erro ao salvar o AssetTag: {e}")    # Registra qualquer erro ocorrido

def get_asset_tag():
    """
    Retorna o AssetTag. Gera um novo se ainda não estiver definido.

    Returns:
        str: AssetTag atual.
    """
    global _asset_tag
    if _asset_tag is None:                      # Verifica se o valor ainda não foi carregado
        _asset_tag = generate_asset_tag()       # Carrega o valor do arquivo
    return _asset_tag                           # Retorna o valor atual do AssetTag

def set_asset_tag(new_tag):
    """
    Atualiza o valor do AssetTag e salva no arquivo.

    Args:
        new_tag (str): Novo valor para o AssetTag.
    """
    global _asset_tag
    _asset_tag = new_tag            # Atualiza a variável global com o novo valor
    save_asset_tag()                # Salva o novo valor no arquivo



def get_chassis_type():
    """
    Determina o ChassisType da Raspberry Pi.

    Returns:
        str: Tipo físico do chassi, por padrão "StandAlone".
            - "StandAlone" para dispositivos independentes e autossuficientes
            - "Enclosure" para caixas que contêm componentes ou dispositivos
            - "RackMount" para instalação em rack
            - "Blade" para servidores blade
    """
    chassis_type = "StandAlone"  
    return chassis_type       


def get_sku():
    """
    Retorna o SKU (Stock Keeping Unit) do dispositivo.

    Returns:
        str: Código SKU do dispositivo. Valor fixo, pois não é possível obter automaticamente.
    """
    sku = "6914260"      # Tentar pegar o valor de forma automatica usando o check_output
    return sku


def get_part_number():
    """
    Retorna o número de peça (Part Number) do dispositivo.

    Returns:
        str: Número de peça do dispositivo. Valor fixo, pois não está disponível diretamente no hardware.
    """
    part_number = "832-6274"    # Informação fornecida na especificação do fabricante. 
                                # Aparentemente, não está disponível diretamente no hardware
    return part_number



def get_power():
    """
    Retorna as propriedades de energia do sistema.

    Returns:
        dict: Dicionário com informações sobre fontes de alimentação e sensores de tensão.
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
    Retorna as propriedades térmicas do sistema.

    Returns:
        dict: Dicionário com informações sobre temperaturas do sistema.
    """
    return {
        "Temperatures": [
            {
                "Name": "CPU Temperature",
                "ReadingsCelsius": f"{float(cpu_temp()):.1f}",
                "Status": {
                    "Health": temp_health(),
                    "State": "Enabled"
                }
            }
        ],
    }

def get_system_type():
    """
    Retorna o tipo de sistema representado pelo recurso ComputerSystem.

    Returns:
        str: Tipo do sistema, por padrão "Physical".
    """
    return "Physical"

# Valores iniciais padrão
data_store = {
    "ServiceEnabled": True,
    "AccountLockoutCounterResetAfter": 30,
    "AccountLockoutCounterResetEnabled": True,
    "AccountLockoutDuration": 60,
    "AccountLockoutThreshold": 5
}

def get_account_service_data():
    """
    Retorna os dados atuais do AccountService.

    Returns:
        dict: Dicionário com os valores atuais do AccountService.
    """
    return data_store

def update_account_service_data(new_data):
    """
    Atualiza os dados do AccountService com as informações enviadas no PATCH.

    Args:
        new_data (dict): Dicionário contendo as chaves e valores a serem atualizados.
    """
    for key, value in new_data.items():
        if key in data_store:
            data_store[key] = value

#-----------------------------------------------------------------------------------------------------------------------

SETTINGS_FILE = "event_service_settings.json"

def load_settings():
    """
    Carrega as configurações do serviço de eventos a partir de um arquivo JSON.

    Returns:
        dict: Dicionário com as configurações carregadas. Retorna um dicionário vazio em caso de erro ou se o arquivo não existir.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar as configurações: {e}")
            return {}
    else:
        return {}

def save_settings(settings):
    """
    Salva as configurações do serviço de eventos em um arquivo JSON.

    Args:
        settings (dict): Dicionário com as configurações a serem salvas.
    """
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar as configurações: {e}")

# Funções específicas para DeliveryRetryAttempts
def get_delivery_retry_attempts():
    """
    Retorna o número de tentativas de reentrega configuradas para eventos.

    Returns:
        int: Número de tentativas de reentrega. Valor padrão é 3.
    """
    settings = load_settings()
    return settings.get("DeliveryRetryAttempts", 3)

def set_delivery_retry_attempts(value):
    """
    Atualiza o número de tentativas de reentrega para eventos.

    Args:
        value (int): Novo valor para tentativas de reentrega.
    """
    settings = load_settings()
    settings["DeliveryRetryAttempts"] = value
    save_settings(settings)

# Funções específicas para DeliveryRetryIntervalSeconds
def get_delivery_retry_interval_seconds():
    """
    Retorna o intervalo (em segundos) entre tentativas de reentrega de eventos.

    Returns:
        int: Intervalo em segundos. Valor padrão é 5.
    """
    settings = load_settings()
    return settings.get("DeliveryRetryIntervalSeconds", 5)

def set_delivery_retry_interval_seconds(value):
    """
    Atualiza o intervalo entre tentativas de reentrega de eventos.

    Args:
        value (int): Novo valor para o intervalo em segundos.
    """
    settings = load_settings()
    settings["DeliveryRetryIntervalSeconds"] = value
    save_settings(settings)

# Funções específicas para ServiceEnabled
def get_service_enabled():
    """
    Retorna o status do serviço de eventos (habilitado ou não).

    Returns:
        bool: True se o serviço estiver habilitado, False caso contrário. Valor padrão é True.
    """
    settings = load_settings()
    return settings.get("ServiceEnabled", True)

def set_service_enabled(value):
    """
    Atualiza o status do serviço de eventos.

    Args:
        value (bool): True para habilitar, False para desabilitar.
    """
    settings = load_settings()
    settings["ServiceEnabled"] = value
    save_settings(settings)

#-----------------------------------------------------------------------------------------------------------------------

# Caminho do arquivo de logs
LOG_FILE = "log_entries.json"

def load_log_entries():
    """
    Carrega as entradas de log do arquivo JSON.

    Returns:
        list: Lista de dicionários representando as entradas de log.
              Retorna uma lista vazia se o arquivo não existir ou estiver vazio/corrompido.
    """
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"Erro ao carregar log entries: {e}")
        return []

def save_log_entries(entries):
    """
    Salva as entradas de log no arquivo JSON.

    Args:
        entries (list): Lista de dicionários representando as entradas de log.
    """
    try:
        with open(LOG_FILE, "w") as file:
            json.dump(entries, file, indent=4)
    except Exception as e:
        print(f"Erro ao salvar log entries: {e}")

def create_log_entry(entry_type, severity, message, message_id=None, event_id=None, entry_code=None):
    """
    Cria uma nova entrada de log e a salva no arquivo.

    Args:
        entry_type (str): Tipo da entrada de log (ex: 'Event', 'Alert').
        severity (str): Severidade do evento (ex: 'OK', 'Warning', 'Critical').
        message (str): Mensagem descritiva do evento.
        message_id (str, optional): Identificador da mensagem.
        event_id (str, optional): Identificador do evento.
        entry_code (str, optional): Código da entrada.

    Returns:
        dict: Dicionário representando a nova entrada de log criada.
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
    Limpa todas as entradas de log do arquivo JSON.

    Esta função sobrescreve o arquivo de log com uma lista vazia.
    """
    try:
        # Verifica se o arquivo de logs existe
        if os.path.exists(LOG_FILE):
            # Escreve uma lista vazia no arquivo para limpar os logs
            with open(LOG_FILE, 'w') as log_file:
                json.dump([], log_file)
            print("Logs limpos com sucesso!")
        else:
            print(f"Arquivo {LOG_FILE} não encontrado, nada para limpar.")
    except Exception as e:
        print(f"Erro ao limpar os logs: {e}")


def get_max_records():
    """
    Retorna o número máximo de registros de log suportados.

    Returns:
        int: Número máximo de registros.
    """
    return 1000  # Número máximo de registros suportados

def get_overwrite_policy():
    """
    Retorna a política de sobrescrita dos logs.

    Returns:
        str: Política de sobrescrita (ex: 'WrapsWhenFull').
    """
    return "WrapsWhenFull"  # Política de sobrescrita

#-----------------------------------------------------------------------------------------------------------------------

# CommandShell
def get_command_shell_service_enabled():
    """
    Retorna se o serviço CommandShell está habilitado.

    Returns:
        bool: True se o serviço estiver habilitado, False caso contrário.
    """
    return True  # Padrão habilitado

def set_command_shell_service_enabled(value):
    """
    Atualiza o status do serviço CommandShell.

    Args:
        value (bool): True para habilitar, False para desabilitar.
    """
    # Lógica para atualizar a configuração
    print(f"CommandShell ServiceEnabled atualizado para {value}")

def get_command_shell_max_sessions():
    """
    Retorna o número máximo de sessões concorrentes permitidas para o CommandShell.

    Returns:
        int: Número máximo de sessões concorrentes.
    """
    return 5  # Número máximo de sessões concorrentes

def get_command_shell_connect_types():
    """
    Retorna os tipos de conexão suportados pelo CommandShell.

    Returns:
        list: Lista de strings com os tipos de conexão suportados.
    """
    return ["SSH", "Telnet"]  # Tipos suportados


# Arquivos de armazenamento
DATE_TIME_FILE = "datetime.json"
DATE_TIME_OFFSET_FILE = "datetime_offset.json"
SERVICE_ENABLED_FILE = "service_enabled.json"

# DateTime
def get_datetime():
    """
    Retorna o valor atual do DateTime.

    Returns:
        str: Data e hora atual no formato ISO 8601 (UTC), ou valor salvo no arquivo se existir.
    """
    try:
        if os.path.exists(DATE_TIME_FILE):
            with open(DATE_TIME_FILE, "r") as file:
                content = file.read().strip()
                if content:
                    data = json.loads(content)
                    return data.get("DateTime", datetime.utcnow().isoformat() + "Z")
                else:
                    print("Arquivo datetime.json está vazio.")
        return datetime.utcnow().isoformat() + "Z"
    except Exception as e:
        print(f"Erro ao carregar DateTime: {e}")
        return datetime.utcnow().isoformat() + "Z"


def set_datetime(new_datetime):
    """
    Atualiza o valor de DateTime.

    Args:
        new_datetime (str): Nova data/hora no formato ISO 8601.
    """
    if not new_datetime:
        print("DateTime inválido, nada foi salvo.")
        return
    try:
        with open(DATE_TIME_FILE, "w") as file:
            json.dump({"DateTime": new_datetime}, file)
            print(f"DateTime atualizado para {new_datetime}")
    except Exception as e:
        print(f"Erro ao atualizar DateTime: {e}")


# DateTimeLocalOffset
def get_datetime_offset():
    try:
        if os.path.exists(DATE_TIME_OFFSET_FILE):
            with open(DATE_TIME_OFFSET_FILE, "r") as file:
                content = file.read().strip()
                if content:
                    data = json.loads(content)
                    return data.get("DateTimeLocalOffset", "+00:00")
                else:
                    print("Arquivo datetime_offset.json está vazio.")
        return "+00:00"
    except Exception as e:
        print(f"Erro ao carregar DateTimeLocalOffset: {e}")
        return "+00:00"

def set_datetime_offset(offset):
    """
    Atualiza o offset de tempo local.

    Args:
        offset (str): Novo offset de tempo local (ex: '+00:00').
    """
    try:
        with open(DATE_TIME_OFFSET_FILE, "w") as file:
            json.dump({"DateTimeLocalOffset": offset}, file)
            print(f"DateTimeLocalOffset atualizado para {offset}")
    except Exception as e:
        print(f"Erro ao atualizar DateTimeLocalOffset: {e}")


# ServiceEnabled
def get_service_enabled():
    """
    Retorna o status atual do ServiceEnabled.

    Returns:
        bool: True se o serviço estiver habilitado, False caso contrário.
    """
    try:
        if os.path.exists(SERVICE_ENABLED_FILE):
            with open(SERVICE_ENABLED_FILE, "r") as file:
                data = json.load(file)
                return data.get("ServiceEnabled", True)  # Padrão True
        return True
    except Exception as e:
        print(f"Erro ao carregar ServiceEnabled: {e}")
        return True

def set_service_enabled(enabled):
    """
    Atualiza o status de ServiceEnabled.

    Args:
        enabled (bool): True para habilitar, False para desabilitar.
    """
    try:
        with open(SERVICE_ENABLED_FILE, "w") as file:
            json.dump({"ServiceEnabled": enabled}, file)
            print(f"ServiceEnabled atualizado para {enabled}")
    except Exception as e:
        print(f"Erro ao atualizar ServiceEnabled: {e}")




#-----------------------------------------------------------------------------------------------------------------------

# Arquivos de armazenamento
FQDN_FILE = "fqdn.json"
HTTPS_CONFIG_FILE = "https_config.json"

# FQDN
def get_fqdn():
    """
    Retorna o Fully Qualified Domain Name (FQDN).

    Se o arquivo não existir ou estiver corrompido, retorna o FQDN do sistema obtido via socket.

    Returns:
        str: FQDN salvo no arquivo ou o FQDN do sistema.
    """
    try:
        # Verifica se o arquivo FQDN_FILE existe
        if os.path.exists(FQDN_FILE):
            with open(FQDN_FILE, "r") as file:
                data = json.load(file)  # Carrega o JSON do arquivo
                return data.get("FQDN", socket.getfqdn())  # Retorna o valor ou o FQDN do sistema
        else:
            # Retorna o FQDN do sistema se o arquivo não existir
            return socket.getfqdn()
    except json.JSONDecodeError as e:
        # Captura erros no formato JSON
        print(f"Erro ao decodificar o arquivo FQDN: {e}")
        return socket.getfqdn()
    except Exception as e:
        # Captura outros erros genéricos
        print(f"Erro ao carregar FQDN: {e}")
        return socket.getfqdn()

def set_fqdn(fqdn):
    """
    Atualiza o FQDN.

    Args:
        fqdn (str): Novo Fully Qualified Domain Name a ser salvo.
    """
    try:
        with open(FQDN_FILE, "w") as file:
            json.dump({"FQDN": fqdn}, file)
            print(f"FQDN atualizado para {fqdn}")
    except Exception as e:
        print(f"Erro ao atualizar FQDN: {e}")


# HTTPS.Port
def get_https_port():
    """
    Retorna a porta HTTPS.

    Returns:
        int: Porta HTTPS configurada. Valor padrão é 443.
    """
    try:
        if os.path.exists(HTTPS_CONFIG_FILE):
            with open(HTTPS_CONFIG_FILE, "r") as file:
                data = json.load(file)
                return data.get("Port", 443)  # Porta padrão 443
        return 443
    except Exception as e:
        print(f"Erro ao carregar HTTPS.Port: {e}")
        return 443

def set_https_port(port):
    """
    Atualiza a porta HTTPS.

    Args:
        port (int): Nova porta HTTPS a ser salva.
    """
    try:
        config = {"Port": port, "ProtocolEnabled": get_https_protocol_enabled()}
        with open(HTTPS_CONFIG_FILE, "w") as file:
            json.dump(config, file)
            print(f"HTTPS.Port atualizado para {port}")
    except Exception as e:
        print(f"Erro ao atualizar HTTPS.Port: {e}")


# HTTPS.ProtocolEnabled
def get_https_protocol_enabled():
    """
    Retorna o status do protocolo HTTPS.

    Returns:
        bool: True se o protocolo HTTPS está habilitado, False caso contrário. Padrão True.
    """
    try:
        if os.path.exists(HTTPS_CONFIG_FILE):
            with open(HTTPS_CONFIG_FILE, "r") as file:
                data = json.load(file)
                return data.get("ProtocolEnabled", True)  # Padrão True
        return True
    except Exception as e:
        print(f"Erro ao carregar HTTPS.ProtocolEnabled: {e}")
        return True

def set_https_protocol_enabled(enabled):
    """
    Atualiza o status do protocolo HTTPS.

    Args:
        enabled (bool): True para habilitar, False para desabilitar.
    """
    try:
        config = {"Port": get_https_port(), "ProtocolEnabled": enabled}
        with open(HTTPS_CONFIG_FILE, "w") as file:
            json.dump(config, file)
            print(f"HTTPS.ProtocolEnabled atualizado para {enabled}")
    except Exception as e:
        print(f"Erro ao atualizar HTTPS.ProtocolEnabled: {e}")


#-----------------------------------------------------------------------------------------------------------------------


def get_hostname():
    """
    Retorna o hostname do sistema.

    Returns:
        str: Hostname do sistema.
    """
    return socket.gethostname()

def get_kernel_name():
    """
    Retorna o nome do kernel do sistema operacional.

    Returns:
        str: Nome do kernel (ex: 'Linux').
    """
    return platform.system()

def get_kernel_release():
    """
    Retorna a release do kernel do sistema operacional.

    Returns:
        str: Release do kernel (ex: '5.10.17-v7l+').
    """
    return platform.release()

def get_kernel_version():
    """
    Retorna a versão detalhada do kernel do sistema operacional.

    Returns:
        str: Versão detalhada do kernel.
    """
    return platform.version()

def get_last_boot_time():
    """
    Retorna a data e hora do último boot do sistema.

    Returns:
        str: Data e hora do último boot em formato ISO 8601.
    """
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    return boot_time.isoformat()

def get_metrics():
    """
    Retorna métricas básicas do sistema.

    Returns:
        dict: Dicionário com uso de CPU (%) e memória (GB).
    """
    return {
        "CPUUsage": f"{str(psutil.cpu_percent())}%",
        "MemoryUsage": f"{round(psutil.virtual_memory().used / (1024**3), 2)}GB"
    }

def get_processor_architecture():
    """
    Retorna a arquitetura do processador.

    Returns:
        str: Arquitetura do processador (ex: 'armv7l', 'aarch64').
    """
    return platform.machine()

def get_operating_system_name():
    """
    Retorna o nome completo do sistema operacional.

    Returns:
        str: Nome completo do sistema operacional.
    """
    return platform.platform()

#-----------------------------------------------------------------------------------------------------------------------

# Caminho para o arquivo que armazenará o estado de ServiceEnabled
SERVICE_ENABLED_FILE = "operating_system_metrics_state.json"

# Estado inicial padrão
default_state = {
    "OperatingSystemMetrics": True,
    "EthernetInterfaceMetrics": True,
    "MemoryMetrics": True,
    "ProcessorMetrics": True,
    "VolumePartitionMetrics": True
}

def load_service_enabled_state():
    """
    Carrega o estado de ServiceEnabled do arquivo JSON.

    Returns:
        dict: Dicionário com o estado atual das métricas (ex: quais métricas estão habilitadas).
              Se o arquivo não existir ou estiver corrompido, retorna o estado padrão.
    """
    if os.path.exists(SERVICE_ENABLED_FILE):
        try:
            with open(SERVICE_ENABLED_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            print("Arquivo corrompido. Recriando com o estado padrão.")
            save_service_enabled_state(default_state)
    # Retorna o estado padrão se o arquivo não existir ou estiver corrompido
    return default_state.copy()

def save_service_enabled_state(state):
    """
    Salva o estado de ServiceEnabled no arquivo JSON.

    Args:
        state (dict): Dicionário com o estado das métricas a serem salvas.
    Raises:
        ValueError: Se o dicionário contiver chaves inválidas.
    """
    # Valida as chaves antes de salvar
    valid_keys = default_state.keys()
    if not all(key in valid_keys for key in state.keys()):
        raise ValueError("O estado contém chaves inválidas.")
    
    with open(SERVICE_ENABLED_FILE, "w") as file:
        json.dump(state, file)

# Carregue o estado atual na inicialização
service_enabled_state = load_service_enabled_state()


def get_ethernet_metrics(service_enabled=True):
    """
    Captura métricas obrigatórias das interfaces Ethernet.

    Args:
        service_enabled (bool): Indica se o serviço está habilitado (padrão: True).

    Returns:
        dict or list: Dicionário {"ServiceEnabled": False} se desabilitado, 
                      ou lista de métricas por interface se habilitado.
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
    Captura métricas obrigatórias da memória.

    Args:
        service_enabled (bool): Indica se o serviço está habilitado (padrão: True).

    Returns:
        dict: Dicionário com métricas de memória ou {"ServiceEnabled": False} se desabilitado.
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
    Captura métricas obrigatórias do processador.

    Args:
        service_enabled (bool): Indica se o serviço está habilitado (padrão: True).

    Returns:
        dict: Dicionário com métricas do processador.
    """
    cpu_usage = cpu_usage_percent()
    cpu_util_pct_idle = 100 - cpu_usage


    #A carga geralmente reflete o nível de concorrência, ou seja, quantos processos estão competindo por tempo de CPU.
    # Obtém as médias de carga do sistema
    load1, load5, load15 = psutil.getloadavg()
    cores = psutil.cpu_count(logical=True)
    # Calcula os percentuais com base nos núcleos
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
    Captura métricas obrigatórias dos volumes de armazenamento.

    Args:
        service_enabled (bool): Indica se o serviço está habilitado (padrão: True).

    Returns:
        dict or list: Dicionário {"ServiceEnabled": False} se desabilitado,
                      ou lista de métricas por volume se habilitado.
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
    Verifica se o serviço para uma métrica está habilitado.

    Args:
        metric_name (str): Nome da métrica (ex: 'MemoryMetrics').

    Returns:
        bool: True se a métrica está habilitada, False caso contrário.
    """
    return service_enabled_state.get(metric_name, False)

def get_metrics_timestamp():
    """
    Retorna o timestamp da última atualização das métricas.

    Returns:
        str: Data e hora atual em formato ISO 8601 com sufixo 'Z' (UTC).
    """
    return datetime.utcnow().isoformat() + "Z"

    

#-----------------------------------------------------------------------------------------------------------------------

ssdp_enabled = True

def get_ssdp_enabled():
    return ssdp_enabled

def set_ssdp_enabled(value):
    global ssdp_enabled
    ssdp_enabled = value
