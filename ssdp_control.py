from multiprocessing import Process
from service_discovery import discovery_SSDP
import readings

ssdp_process = None

def start_ssdp():
    """
    Starts the SSDP discovery process if it is not already running.

    Side Effects:
        Updates the global SSDP process handle and spawns a background process.
    """
    global ssdp_process
    if not readings.get_ssdp_enabled():
        print("SSDP desabilitado por configuracao.")
        return

    if ssdp_process is None or not ssdp_process.is_alive():
        ssdp_process = Process(target=discovery_SSDP)
        ssdp_process.start()
        print("SSDP iniciado.")

def stop_ssdp():
    """
    Stops the SSDP discovery process when it is running.

    Side Effects:
        Terminates and joins the process, then clears the global process handle.
    """
    global ssdp_process
    if ssdp_process is not None and ssdp_process.is_alive():
        ssdp_process.terminate()
        ssdp_process.join()
        ssdp_process = None
        print("SSDP finalizado.")
