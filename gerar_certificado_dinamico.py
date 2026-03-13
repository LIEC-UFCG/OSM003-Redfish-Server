import os
import socket
import subprocess

def obter_ip_local():
    """
    Obtém o IP local da máquina.

    Returns:
        str: Endereço IP local detectado. Retorna "127.0.0.1" em caso de erro.
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
    Verifica se o IP atual já está presente no certificado SAN.

    Args:
        cert_file (str): Caminho para o arquivo do certificado.
        ip_esperado (str): IP que deve estar presente no certificado.

    Returns:
        bool: True se o IP estiver no certificado, False caso contrário.
    """
    try:
        resultado = subprocess.check_output(
            ["openssl", "x509", "-in", cert_file, "-noout", "-text"]
        ).decode()
        return f"IP Address:{ip_esperado}" in resultado
    except Exception:
        return False

def certificados_estao_atualizados(ip):
    """
    Verifica se os arquivos de certificado existem e se estão válidos para o IP atual.

    Args:
        ip (str): IP que deve estar presente no certificado.

    Returns:
        bool: True se todos os arquivos existem e o IP está no certificado, False caso contrário.
    """
    arquivos_ok = all(os.path.exists(f) for f in ["domain.key", "domain.csr", "domainSAN.crt", "domain.ext"])
    ip_ok = ip_esta_no_certificado("domainSAN.crt", ip)
    return arquivos_ok and ip_ok

def gerar_certificados(ip):
    """
    Gera certificados SSL para o IP informado.

    Cria os arquivos domain.key, domain.csr, domain.ext e domainSAN.crt usando OpenSSL.

    Args:
        ip (str): IP que será incluído como SAN no certificado.
    """
    print(f"Gerando certificados para IP: {ip}")

    subprocess.run(["openssl", "genrsa", "-out", "domain.key", "2048"], check=True)
    subprocess.run(["openssl", "req", "-new", "-key", "domain.key", "-out", "domain.csr", "-subj", f"/CN={ip}"], check=True)

    with open("domain.ext", "w") as f:
        f.write(f"subjectAltName=IP:{ip}\n")

    subprocess.run([
        "openssl", "x509", "-req", "-days", "365", "-in", "domain.csr",
        "-signkey", "domain.key", "-out", "domainSAN.crt", "-extfile", "domain.ext"
    ], check=True)

    print("Certificados gerados com sucesso.")

def registrar_certificado_no_sistema():
    """
    Copia o certificado gerado para a lista de certificados confiáveis do sistema e atualiza o repositório.

    Side Effects:
        Executa comandos sudo para copiar e registrar o certificado no sistema.
        Imprime mensagens de status no console.
    """
    destino = "/usr/local/share/ca-certificates/redfish.crt"
    try:
        subprocess.run(["sudo", "cp", "domainSAN.crt", destino], check=True)
        subprocess.run(["sudo", "update-ca-certificates"], check=True)
        print("Certificado registrado no sistema com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao registrar certificado no sistema: {e}")