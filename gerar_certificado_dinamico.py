import os
import socket
import subprocess

def obter_ip_local():
    """
    Gets the local IP of the machine.

    Returns:
        str: Local IP address detected. Returns "127.0.0.1" on error.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def ip_esta_no_certificado(cert_file, ip_esperado):
    """
    Checks if the current IP is already present in the certificate SAN.

    Args:
        cert_file (str): Path to certificate file.
        ip_esperado (str): IP that should be present in certificate.

    Returns:
        bool: True if IP is in certificate, False otherwise.
    """
    if not os.path.exists(cert_file):
        return False
    try:
        resultado = subprocess.check_output(
            ["openssl", "x509", "-in", cert_file, "-noout", "-text"],
            stderr=subprocess.DEVNULL
        ).decode()
        return f"IP Address:{ip_esperado}" in resultado
    except Exception:
        return False

def certificados_estao_atualizados(ip):
    """
    Checks if certificate files exist and are valid for current IP.

    Args:
        ip (str): IP that should be present in certificate.

    Returns:
        bool: True if all files exist and IP is in certificate, False otherwise.
    """
    arquivos_ok = all(os.path.exists(f) for f in ["domain.key", "domain.csr", "domainSAN.crt", "domain.ext"])
    ip_ok = ip_esta_no_certificado("domainSAN.crt", ip)
    return arquivos_ok and ip_ok

def gerar_certificados(ip):
    """
    Generates SSL certificates for the provided IP.

    Creates domain.key, domain.csr, domain.ext and domainSAN.crt files using OpenSSL.

    Args:
        ip (str): IP to be included as SAN in certificate.
    """
    print(f"Generating certificates for IP: {ip}")

    subprocess.run(["openssl", "genrsa", "-out", "domain.key", "2048"], check=True)
    subprocess.run(["openssl", "req", "-new", "-key", "domain.key", "-out", "domain.csr", "-subj", f"/CN={ip}"], check=True)

    with open("domain.ext", "w") as f:
        f.write(f"subjectAltName=IP:{ip}\n")

    subprocess.run([
        "openssl", "x509", "-req", "-days", "365", "-in", "domain.csr",
        "-signkey", "domain.key", "-out", "domainSAN.crt", "-extfile", "domain.ext"
    ], check=True)

    print("Certificates generated successfully.")

def registrar_certificado_no_sistema():
    """
    Copies generated certificate to system's trusted certificate list and updates repository.

    Side Effects:
        Executes sudo commands to copy and register certificate in system.
        Prints status messages to console.
    """
    destino = "/usr/local/share/ca-certificates/redfish.crt"
    try:
        subprocess.run(["sudo", "cp", "domainSAN.crt", destino], check=True)
        subprocess.run(["sudo", "update-ca-certificates"], check=True)
        print("Certificate registered in system successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error registering certificate in system: {e}")