from multiprocessing import Process
from service_discovery import discovery_SSDP

ssdp_process = None

def start_ssdp():
    global ssdp_process
    if ssdp_process is None or not ssdp_process.is_alive():
        ssdp_process = Process(target=discovery_SSDP)
        ssdp_process.start()
        print("SSDP iniciado.")

def stop_ssdp():
    global ssdp_process
    if ssdp_process is not None and ssdp_process.is_alive():
        ssdp_process.terminate()
        ssdp_process.join()
        ssdp_process = None
        print("SSDP finalizado.")
