# Importações necessárias para o funcionamento do servidor Flask e funcionalidades adicionais
from flask import Flask, abort, jsonify, request, Response, make_response, send_from_directory, redirect
from multiprocessing import Process
import json
import readings
import redfish_root
import sessionservice
import chassis
import computersystem
import ethernetinterfaces
import accountservice
import distributedcontrolnode
import eventservice
import logservice
import manager
import operatingsystem
import session
import updateservice
import manageraccount
import roles
import eventdestination
import jsonschemas
import os
import container
from auth import requires_authentication, requires_privilege
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
from session import load_sessions, save_sessions
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import FLASK_PORT, FLASK_IP, CERT_FILE, KEY_FILE
import subprocess
from gerar_certificado_dinamico import obter_ip_local, gerar_certificados, certificados_estao_atualizados, registrar_certificado_no_sistema
from flask_talisman import Talisman
from logservice import add_audit_log_entry, add_event_log_entry
from logservice import AUDIT_LOG_FILE, AUTH_LOG_FILE, EVENT_LOG_FILE, ERROR_LOG_FILE
import ssdp_control

from flask import current_app
from flask_limiter.errors import RateLimitExceeded
from flask import jsonify
import logging

RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI")

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, "redfishpi_logs")
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório de logs: {e}")

# Inicializa a aplicação Flask
app = Flask(__name__) 
Talisman(app)


# Função para obter o token de autenticação do cabeçalho da requisição
# Caso o token não esteja presente, utiliza o endereço remoto do cliente
def get_token():
    """
    Obtém o token de autenticação do cabeçalho da requisição.

    Se o token não estiver presente, utiliza o endereço remoto do cliente.

    Returns:
        str: Token de autenticação ou endereço IP do cliente.
    """
    return request.headers.get("X-Auth-Token") or get_remote_address()




# configuração do limiter
limiter = Limiter(
    key_func=get_token,
    app=app,
    default_limits=[],
    storage_uri=RATE_LIMIT_STORAGE_URI if RATE_LIMIT_STORAGE_URI else "memory://"
)

RATE_LIMIT = "1 per second"
ENABLE_RATE_LIMIT = True

def conditional_limit(limit):
    def decorator(func):
        if ENABLE_RATE_LIMIT:
            return limiter.limit(limit)(func)
        return func
    return decorator

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    current_app.logger.warning("Rate limit exceeded: %s", e)
    return jsonify(error="Too many requests"), 429

# Middleware para formatar as respostas JSON de forma indentada

@app.after_request
def pretty_json(response):
    """Esta funcao e um decorator usado pelo flask na formatacao de respostas solicitadas aos endpoints.
    Formata as respostas JSON de forma identada.
    O Content-Type application/json e setado explicitamente.
    
    Args:
        response: resposta do flask para a requisicao http
    Returns:
        response: formatado com json identado
    """
    if (
        response.content_type == "application/json" # Verifica se a resposta é JSON
        and response.get_data(as_text=True)         # Ignora respostas vazias
    ):
        try:
            # Formata o JSON com indentação
            data = json.loads(response.get_data(as_text=True))
            pretty = json.dumps(data, indent=4)
            response.set_data(pretty)
            response.headers["Content-Length"] = len(pretty)    # Atualiza o tamanho do conteúdo
        except Exception:
            pass  # Ignora erros e mantém a resposta original
    return response

# Configuração para evitar o escape de caracteres ASCII no JSON
app.config['JSON_AS_ASCII'] = False 

# Retorna uma mensagem de boas-vindas
@app.route('/')
@conditional_limit(RATE_LIMIT)
def index():
    """
    Rota de apresentação da aplicação Flask.

    Exibe uma mensagem simples de boas-vindas indicando que o serviço RedfishPi está ativo.

    Returns:
        str: Mensagem de boas-vindas.
    """
    return 'Bem Vindo a RedfishPi'

# Rota para o endpoint /redfish, retorna a rota raiz
@app.route('/redfish', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
def redfish():
    """
    Rota para /redfish.

    Returns:
        tuple: Dicionário com o caminho para a versão 1 da API e código HTTP 200.
    """
    return {
        "v1": "/redfish/v1/"
    }, 200

# Obtém os dados do Redfish root
redfish_data = redfish_root.get_redfish_v1()

# Rota para o endpoint /redfish/v1/, retorna os dados do Redfish root
@app.route('/redfish/v1', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)
def get_redfish_root():
    """
    Rota raiz.

    Returns:
        flask.Response: Resposta JSON formatada com os dados do Redfish root.
    """
    return Response(
        json.dumps(redfish_data, indent=2, ensure_ascii=False), # Formata o JSON
        mimetype='application/json'                             # Define o tipo de conteúdo como JSON
    )

# Rota para métodos não suportados no endpoint /redfish/v1/
@app.route('/redfish/v1', methods=['POST', 'PATCH', 'DELETE', 'FAKEMETHODFORTEST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def redfish_root_unsupported_methods():
    """
    Rota para métodos não suportados no endpoint /redfish/v1/.

    Returns:
        flask.Response: Mensagem de erro e código HTTP 405.
    """
    return jsonify({"error": "Method not allowed"}), 405

# Rota para o endpoint /redfish/v1/$metadata, retorna o arquivo de metadados
@app.route('/redfish/v1/$metadata', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def metadata():
    """
    Rota para o endpoint /redfish/v1/$metadata, retorna o arquivo de metadados.

    Returns:
        tuple: Conteúdo do arquivo XML e cabeçalho ou mensagem de erro e código 404.
    """
    try:
        with open('schemas/v1/metadata.xml', 'r') as file:
            return file.read(), 200, {'Content-Type': 'application/xml'}
    except FileNotFoundError:
        return jsonify({"error": "$metadata file not found"}), 404

# Rota para servir arquivos de esquema do diretório schemas/v1
@app.route('/schemas/v1/<path:filename>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def serve_schemas_v1(filename):
    """
    Serve arquivos de esquemas do diretório 'schemas/v1'.

    Args:
        filename (str): Nome do arquivo a ser buscado no diretório.

    Returns:
        flask.Response: Arquivo de schema ou mensagem de erro 404.
    """
    try:
        return send_from_directory('schemas/v1', filename)
    except FileNotFoundError:
        return jsonify({"error": f"Schema file '{filename}' not found"}), 404

# Rota para servir o favicon da aplicação
@app.route('/favicon.ico', strict_slashes=False)
@conditional_limit(RATE_LIMIT) 
def favicon():
    """
    Rota para servir o favicon da aplicação.

    Returns:
        flask.Response: Arquivo favicon.ico.
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

# Rota para o endpoint /redfish/v1/odata, retorna informações básicas do OData
@app.route('/redfish/v1/odata', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)  
def odata():
    """
    Rota para o endpoint /redfish/v1/odata, retorna informações básicas do OData.

    Returns:
        flask.Response: JSON com contexto OData e valor mínimo.
    """
    response = {
        "@odata.context": "/redfish/v1/$metadata",
        "value": []  # Valor mínimo, pode ser expandido conforme necessário
    }
    return jsonify(response), 200

# Obtém o ID do sistema a partir do módulo readings
system_id = readings.machine_id()

# Rota para o endpoint /redfish/v1/AccountService/, permite GET e PATCH
@app.route('/redfish/v1/AccountService', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("AccountService")
def account_service():
    """
    Rota para o endpoint /redfish/v1/AccountService/.

    Permite obter (GET) ou atualizar (PATCH) informações do AccountService.

    Returns:
        flask.Response: 
            - GET: Retorna os dados do AccountService.
            - PATCH: Atualiza o estado do AccountService e retorna mensagem de sucesso ou erro.
    """
    if request.method == 'GET':
        return accountservice.get_account_service()
    elif request.method == 'PATCH':
        return accountservice.update_account_service(request.json)


# Rota para o endpoint /redfish/v1/AccountService/Accounts, permite GET e POST
@app.route('/redfish/v1/AccountService/Accounts', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ManagerAccountCollection")
def accounts_collection():
    """
    Rota para o endpoint /redfish/v1/AccountService/Accounts.

    Permite obter (GET) a lista de contas ou criar (POST) uma nova conta.

    Returns:
        flask.Response:
            - GET: Retorna a lista de contas.
            - POST: Retorna a nova conta criada.
    """
    if request.method == 'GET':
        accounts = manageraccount.get_accounts()
        return accounts, 200
    elif request.method == 'POST':
        new_account, status_code = manageraccount.create_account()

        if status_code == 201 and "UserName" in new_account:
            add_audit_log_entry(
                system_id=system_id,
                logservice_id="Log1",
                message=f"User {new_account['UserName']} created",
                user_name=request.headers.get("X-Auth-Token", "admin"),
                severity="OK",
                message_id="Audit.User.Create"
            )
        else:
            logging.warning(f"Failed to create user: {new_account}")

        return new_account, status_code

# Rota para o endpoint /redfish/v1/AccountService/Accounts/<account_id>, permite GET, PATCH e DELETE
@app.route('/redfish/v1/AccountService/Accounts/<account_id>', methods=['GET', 'PATCH', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ManagerAccount")
def account_detail(account_id):
    """
    Rota para o endpoint /redfish/v1/AccountService/Accounts/<account_id>.

    Permite obter (GET), atualizar (PATCH) ou excluir (DELETE) uma conta específica.

    Args:
        account_id (str): ID da conta.

    Returns:
        flask.Response:
            - GET: Retorna os dados da conta.
            - PATCH: Atualiza a conta.
            - DELETE: Remove a conta.
    """
    if request.method == 'GET':
        return manageraccount.get_account(account_id)
    elif request.method == 'PATCH':
        add_audit_log_entry(
            system_id=system_id,
            logservice_id="Log1",
            message=f"User {account_id} updated",
            user_name=request.headers.get("X-Auth-Token", "admin"),
            severity="OK",
            message_id="Audit.User.Update"
        )
        return manageraccount.update_account(account_id)
    elif request.method == 'DELETE':
        add_audit_log_entry(
            system_id=system_id,
            logservice_id="Log1",
            message=f"User {account_id} deleted",
            user_name=request.headers.get("X-Auth-Token", "admin"),
            severity="OK",
            message_id="Audit.User.Delete"
        )
        return manageraccount.delete_account(account_id)

# Rota para o endpoint /redfish/v1/AccountService/Roles, retorna os papéis disponíveis
@app.route('/redfish/v1/AccountService/Roles', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("RoleCollection")
def roles_collection():
    """
    Rota para o endpoint /redfish/v1/AccountService/Roles.

    Retorna a lista de papéis (roles) disponíveis.

    Returns:
        flask.Response: Lista de papéis disponíveis.
    """
    return roles.get_roles()

# Rota para o endpoint /redfish/v1/AccountService/Roles/<role_id>, retorna detalhes de um papel específico
@app.route('/redfish/v1/AccountService/Roles/<role_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Role")
def role_detail(role_id):
    """
    Rota para o endpoint /redfish/v1/AccountService/Roles/<role_id>.

    Retorna detalhes de um papel (role) específico.

    Args:
        role_id (str): ID do papel.

    Returns:
        flask.Response: Detalhes do papel solicitado.
    """
    return roles.get_role(role_id)

# Rota para o endpoint /redfish/v1/Chassis/, retorna informações sobre os chassis
@app.route('/redfish/v1/Chassis', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ChassisCollection")
def get_chassis():
    """
    Rota para o endpoint /redfish/v1/Chassis/.

    Retorna informações sobre todos os chassis disponíveis no sistema.

    Returns:
        flask.Response: JSON com a coleção de chassis no formato Redfish.
    """
    return chassis.get_chassis()

# Carrega o AssetTag ao iniciar o servidor
readings.load_asset_tag()

# Rota para o endpoint /redfish/v1/Chassis/<machine_id>, permite GET e PATCH
@app.route('/redfish/v1/Chassis/<system_id>', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Chassis")
def get_chassis_id(system_id):
    """
    Rota para o endpoint /redfish/v1/Chassis/<machine_id>.

    Permite obter (GET) ou atualizar (PATCH) informações detalhadas do chassi identificado pelo machine_id.

    Returns:
        flask.Response:
            - GET: Retorna informações detalhadas do chassi.
            - PATCH: Atualiza o AssetTag do chassi e retorna mensagem de sucesso ou erro.
    """
    if request.method == 'GET':
        return chassis.get_chassis_id()
    elif request.method == 'PATCH':
        data = request.get_json()
        if "AssetTag" in data:
            readings.set_asset_tag(data["AssetTag"]) # Atualiza o AssetTag
            return jsonify({
                "Message": "AssetTag atualizado com sucesso!",
                "AssetTag": data["AssetTag"]
            }), 200
        else:
            return jsonify({"Message": "Campo AssetTag não fornecido"}), 400

# Rota para o endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem, retorna informações térmicas
@app.route('/redfish/v1/Chassis/<system_id>/ThermalSubsystem', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ThermalSubsystem")
def get_chassis_id_thermalSubsystem(system_id):
    """
    Rota para o endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem.

    Retorna informações do subsistema térmico do chassi.

    Returns:
        flask.Response: JSON com informações do subsistema térmico.
    """
    return chassis.get_thermalSubsystem()

# Rota para o endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem/ThermalMetrics, permite GET e PATCH
@app.route('/redfish/v1/Chassis/<system_id>/ThermalSubsystem/ThermalMetrics', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ThermalMetrics")
def get_chassis_id_thermalMetrics(system_id):
    """
    Rota para o endpoint /redfish/v1/Chassis/<machine_id>/ThermalSubsystem/ThermalMetrics.

    Retorna as métricas térmicas do chassi.

    Returns:
        flask.Response: JSON com as métricas térmicas do chassi.
    """
    return chassis.get_thermalMetrics()

# Rota para o endpoint /redfish/v1/Chassis/<machine_id>/PowerSubSystem, retorna informações de energia
@app.route('/redfish/v1/Chassis/<system_id>/PowerSubsystem', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("PowerSubsystem")
def get_chassis_id_powerSubsystem(system_id):
    """
    Rota para o endpoint /redfish/v1/Chassis/<machine_id>/PowerSubsystem.

    Retorna informações do subsistema de energia do chassi.

    Returns:
        flask.Response: JSON com informações do subsistema de energia.
    """
    return chassis.get_powerSubsystem()

# Rota para o endpoint /redfish/v1/Chassis/<machine_id>/Sensors, retorna informações de sensores
@app.route('/redfish/v1/Chassis/<system_id>/Sensors', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Sensor")
def get_chassis_id_sensors(system_id):
    """
    Rota para o endpoint /redfish/v1/Chassis/<machine_id>/Sensors.

    Retorna informações dos sensores do chassi.

    Returns:
        flask.Response: JSON com leituras dos sensores do chassi.
    """
    return chassis.get_sensors()
#-----------------------------------------------------------------------------------------------------------------------

# Rota para o endpoint /redfish/v1/JsonSchemas/
# Retorna uma lista de esquemas JSON disponíveis para a API
@app.route('/redfish/v1/JsonSchemas', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("JsonSchemaFileCollection")
def get_json_schema_file():
    """Rota para o endpoint /redfish/v1/JsonSchemas/
    
    Returns:
        return: Retorna uma lista de esquemas JSON disponiveis para a API
    """
    return jsonschemas.get_json_schemas()

# Rota para o endpoint /redfish/v1/JsonSchemas/Chassis.v1_26_0
# Retorna o esquema JSON específico para o chassis na versão 1.26.0
@app.route('/redfish/v1/JsonSchemas/Chassis.v1_26_0', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("JsonSchemaFile")
def get_json_schema_chassis():
    """ Rota para o endpoint /redfish/v1/JsonSchemas/Chassis.v1_26_0

    Returns:
        return: Retorna o esquema JSON especifico para o chassis na versao 1.26.0
    """
    return jsonschemas.get_chassis_schemas()

# Rota para o endpoint /redfish/v1/Systems/
# Retorna informações sobre os sistemas computacionais disponíveis
@app.route('/redfish/v1/Systems', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystemCollection")
def get_computer():
    """ Rota para o endpoint /redfish/v1/Systems/, permite o metodo GET

    Returns:
        return: Retorna informacoes sobre os systemas computacionais disponiveis
    """
    return computersystem.get_computer()

# Rota para o endpoint /redfish/v1/Systems/<machine_id>/Actions/ComputerSystem.Reset
# Permite reiniciar o sistema computacional identificado pelo machine_id
@app.route('/redfish/v1/Systems/<system_id>/Actions/ComputerSystem.Reset', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def reset_system(system_id):
    """ Rota para o endpoint /redfish/v1/Systems/<machine_id>/Actions/ComputerSystem.Reset

    Returns:
        return: Permite reiniciar o sistema computacional identificado pelo machine_id
    """
    add_event_log_entry(
        system_id=system_id,
        logservice_id="Log1",
        message="System reset executed",
        user_name=request.headers.get("X-Auth-Token", "admin"),
        severity="OK",
        message_id="Event.System.Reset"
    )
    return computersystem.reset_computer(system_id)

# Rota para o endpoint /redfish/v1/Systems/<machine_id>
# Retorna informações detalhadas sobre o sistema computacional identificado pelo machine_id
@app.route('/redfish/v1/Systems/<system_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def get_computer_id(system_id):
    """ Rota para o endpoint /redfish/v1/Systems/<machine_id>

    Returns:
        return: Retorna informacoes detalhadas sobre o sistema computacional identificado pelo machine_id
    """
    return computersystem.get_computer_system()

# Rota para o endpoint /redfish/v1/Systems/<machine_id>/Processors
# Retorna informações sobre os processadores do sistema computacional
@app.route('/redfish/v1/Systems/<system_id>/Processors', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ProcessorCollection")
def get_systems_id_processors(system_id):
    """ Rota para o endpoint /redfish/v1/System/<machine_id>/Processors, permite o metodo GET

    Returns:
        return: Retorna informacoes sobre os processadores do sistema computacional
    """
    return computersystem.get_systems_id_processors()

# Rota para o endpoint /redfish/v1/Systems/<machine_id>/Processors/CPU1
# Retorna informações detalhadas sobre o processador CPU1 do sistema computacional
@app.route('/redfish/v1/Systems/<system_id>/Processors/CPU1', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Processor")
def get_systems_id_processors_cpu1(system_id):
    """ Rota para o endpoint /redfish/v1/Systems/<machine_id>/Processors/CPU1, permite o metodo GET

    Returns:
        return: Retorna informacoes detalhadas sobre o processador CPU1 do sistema computacional
    """
    return computersystem.get_systems_id_processors_cpu1()

# Rota para o endpoint /redfish/v1/Systems/<machine_id>/SimpleStorage
# Retorna informações sobre os dispositivos de armazenamento simples do sistema
@app.route('/redfish/v1/Systems/<system_id>/SimpleStorage', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("SimpleStorageCollection")
def get_systems_id_simpleStorage(system_id):
    """ Rota para o endpoint /redfish/v1/System/<machine_id>/SimpleStorage, permite o metodo GET

    Returns:
        return: Retorna informacoes sobre os dispositivos de armazenamento simples do sistema
    """
    return computersystem.get_systems_id_simpleStorage()


storage_functions = computersystem.dynamic_storage_funcs() # Obtém funções dinâmicas de armazenamento

for func in storage_functions: # Itera sobre as funções de armazenamento
    # Registra cada função como uma rota no Flask
    # O nome da função é usado para criar a rota, removendo o prefixo 'storage_'
    # O método HTTP é definido como GET
    route = f"/redfish/v1/Systems/{readings.machine_id()}/SimpleStorage/{func.__name__.replace('storage_', '')}"
    # Encadeia manualmente os decoradores
    decorated_func = limiter.limit("1 per second")(
                        requires_privilege("SimpleStorage")(
                            requires_authentication(func)
                        ))
    app.route(route, methods=['GET'])(decorated_func)

# Rota para obter informações do sistema operacional
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def get_operating_system(system_id):
    """ Rota para obter informacoes do sistema operacional, permite o metodo GET
    Returns:
        return: Retorna um JSON referente ao endpoint /redfish/v1/$metadata#OperatingSystem.OperatingSystem
    """
    return operatingsystem.get_operating_system()


# Permite obter e atualizar métricas do sistema operacional
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/OperatingSystemMetrics', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def operating_system_metrics(system_id):
    """ Permite obter e atualizar metricas do sistema operacional, permite GET e PATCH

    Returns:
        return: Retorna um JSON referente ao endpoint /redfish/v1/$metadata#OperatingSystemMetrics.OperatingSystemMetrics
        return: Atualiza o valor de ServiceEnabled em qualquer categoria.
    """
    if request.method == 'GET':
        return operatingsystem.get_operating_system_metrics()
    elif request.method == 'PATCH':
        data = request.json
        return operatingsystem.update_service_enabled(data)

# Permite obter informações sobre os containers do sistema operacional
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def containers_collection(system_id):
    """ Permite obter informacoes sobre os containers do sistema operacional, permite o metodo GET
    
    Args: 
        system_id: Recebe como parametro o UUID do dispositivo.
    Returns:
        return: Retorna a coleção de containers em execução
    """
    return container.get_containers(system_id)

# Permite obter informações detalhadas sobre um container específico
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def container_detail(system_id, container_id):
    """ Permite obter informacoes detalhadas sobre um container especifico, permite o metodo GET

    Args:
        system_id: UUID do dispositivo
        container_id: id do container existente no dispositivo
    Returns:
        return: Retorna detalhes de um container específico
    """
    return container.get_container(system_id, container_id)

# Permite reiniciar um container específico
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Reset', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def reset_container(system_id, container_id):
    """ Permite reiniciar um container especifico, permite o metodo POST

    Args:
        container_id: id do container existente no dispositivo
    Returns:
        return: Reinicia um container
    """
    return container.reset_container(container_id)

# Permite iniciar um container específico
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Start', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def start_container(system_id, container_id):
    """ Permite iniciar um container especifico, permite o metodo POST

    Args:
        container_id: id do container existente no dispositivo
    Returns:
        return: Inicia um container
    """
    return container.start_container(container_id)

# Permite parar um container específico
@app.route('/redfish/v1/Systems/<system_id>/OperatingSystem/Containers/<container_id>/Actions/Container.Stop', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def stop_container(system_id, container_id):
    """ Permite parar um container especifico, permite o metodo POST

    Args:
        container_id: id do container existente no dispositivo
    Returns:
        return: Para um container
    """
    return container.stop_container(container_id)

# Permite obter informações sobre os logs do sistema
@app.route('/redfish/v1/Systems/<system_id>/LogServices', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogServiceCollection")
def log_services_collection(system_id):
    """ Permite obter informacoes sobre os logs do sistema

    Args:
        system_id: UUID do dispositivo
    Returns:
        return: Retorna a coleção de serviços de log disponíveis para um sistema específico
    """
    return logservice.get_log_services_collection(system_id)

# Permite obter informações detalhadas sobre um log específico
@app.route('/redfish/v1/Systems/<system_id>/LogServices/<log_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def log_service_detail(system_id, log_id):
    """ Permite obter informacoes detalhadas sobre um log especifico

    Args:
        system_id: UUID do dispositivo
        log_id: id unico do log a ser detalhado
    Returns:
        return: Retorna um serviço de log específico
    """
    return logservice.get_log_service_detail(system_id, log_id)

# Permite obter informações sobre as entradas de log de um log específico
@app.route('/redfish/v1/Systems/<system_id>/LogServices/Log1/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def log_entries(system_id):
    """ Permite obter informacoes sobre as entradas de log de um log especifico.

    Args:
        system_id: UUID do dispositivo
    Returns:
        return: Retorna a coleção de Log Entries para um Log específico.
    """
    return logservice.get_log_entries(system_id, "Log1")

# Permite obter informações detalhadas sobre uma entrada de log específica
@app.route('/redfish/v1/Systems/<system_id>/LogServices/Log1/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntry")
def log_entry_detail(system_id, event_id):
    """ Permite obter informacoes detalhadas sobre uma entrada de log especifica

    Args:
        system_id: UUID do dispositivo
        event_id: id unico do evento
    Returns:
        return: Retorna um LogEntry específico
    """
    return logservice.get_log_entry_by_id(system_id, "Log1", event_id)

# Permite criar uma nova entrada de log em um log específico
@app.route('/redfish/v1/Systems/<system_id>/LogServices/<logservice_id>/Entries', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def create_log_entry(system_id, logservice_id):
    """ Permite criar uma nova entrada de log em um log especifico, permite o metodo POST
    Cria um novo LogEntry no LogService
    
    Args:
        system_id: UUID do dispositivo
        logservice_id: id unico para logservice
    Returns:
        return: Adiciona um novo LogEntry
    """
    try:
        data = request.get_json()
        username = data.get("UserName")

        required_fields = ["EntryType", "Severity", "Message", "MessageId"] # Campos obrigatórios
        # Verifica se os campos obrigatórios estão presentes
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Cria uma nova entrada de log
        new_entry = logservice.add_log_entry( 
            system_id=system_id,
            logservice_id=logservice_id,
            entry_type=data["EntryType"],
            severity=data["Severity"],
            message=data["Message"],
            message_id=data["MessageId"],
            user_name=username
        )

        return jsonify(new_entry), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create log entry: {str(e)}"}), 500


def load_log_file(log_file):
    import json
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
                if isinstance(logs, list):
                    return logs
        except Exception:
            pass
    return []

def get_log_entry_by_eventid(log_file, system_id, log_type, event_id):
    logs = load_log_file(log_file)
    for log in logs:
        if str(log["EventId"]) == str(event_id):
            response = {
                "@odata.type": "#LogEntry.v1_17_0.LogEntry",
                "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/{log_type}/Entries/{event_id}",
                "Id": log["EventId"],
                "Name": log["Name"],
                "EntryType": log["EntryType"],
                "Severity": log["Severity"],
                "Created": log["Created"],
                "Resolved": log["Resolved"],
                "Message": log["Message"],
                "MessageId": log["MessageId"],
                "UserName": log.get("UserName"),
                "MessageArgs": log["MessageArgs"]
            }
            return jsonify(response), 200
    return jsonify({"error": "Log entry not found"}), 404

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def audit_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuditLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def auth_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "AuthLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def event_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "EventLog")

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def error_log_service_detail(system_id):
    return logservice.get_log_service_detail(system_id, "ErrorLog")


@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def audit_log_entries(system_id):
    logs = load_log_file(AUDIT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuditLog/Entries",
        "Name": "Audit Log Entries Collection",
        "Members": [{"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuditLog/Entries/{log['EventId']}"} for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def auth_log_entries(system_id):
    logs = load_log_file(AUTH_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuthLog/Entries",
        "Name": "Auth Log Entries Collection",
        "Members": [{"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/AuthLog/Entries/{log['EventId']}"} for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def event_log_entries(system_id):
    logs = load_log_file(EVENT_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/EventLog/Entries",
        "Name": "Event Log Entries Collection",
        "Members": [{"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/EventLog/Entries/{log['EventId']}"} for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog/Entries', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntryCollection")
def error_log_entries(system_id):
    logs = load_log_file(ERROR_LOG_FILE)
    response = {
        "@odata.type": "#LogEntryCollection.LogEntryCollection",
        "@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/ErrorLog/Entries",
        "Name": "Error Log Entries Collection",
        "Members": [{"@odata.id": f"/redfish/v1/Systems/{system_id}/LogServices/ErrorLog/Entries/{log['EventId']}"} for log in logs],
        "Members@odata.count": len(logs)
    }
    return jsonify(response)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuditLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntry")
def audit_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUDIT_LOG_FILE, system_id, "AuditLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/AuthLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntry")
def auth_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(AUTH_LOG_FILE, system_id, "AuthLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/EventLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntry")
def event_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(EVENT_LOG_FILE, system_id, "EventLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/ErrorLog/Entries/<event_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogEntry")
def error_log_entry_detail(system_id, event_id):
    return get_log_entry_by_eventid(ERROR_LOG_FILE, system_id, "ErrorLog", event_id)

@app.route('/redfish/v1/Systems/<system_id>/LogServices/<log_id>/Actions/LogService.ClearLog', methods=['POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("LogService")
def clear_log_action(system_id, log_id):
    log_files = {
        "AuditLog": AUDIT_LOG_FILE,
        "AuthLog": AUTH_LOG_FILE,
        "EventLog": EVENT_LOG_FILE,
        "ErrorLog": ERROR_LOG_FILE
    }
    log_file = log_files.get(log_id)
    if not log_file:
        return jsonify({"error": "Invalid log id"}), 404

    try:
        with open(log_file, "w") as f:
            f.write("[]")
        add_audit_log_entry(
            system_id=system_id,
            logservice_id=log_id,
            message=f"Log {log_id} cleared by user",
            user_name=get_authenticated_username(),
            severity="OK",
            message_id="Audit.Log.Cleared"
        )
        return '', 204
    except Exception as e:
        return jsonify({"error": f"Failed to clear log: {str(e)}"}), 500


# Rota para obter informações do DCN
@app.route('/redfish/v1/DistributedControlNode', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ComputerSystem")
def distributed_control_node_endpoint():
    """ Rota para obter informacoes do DCN com uso do metodo GET, como o tipo de nó O-PAS, pode ser "DCN" ou outro
        
    Returns:
        return: JSON com informacoes sobre o DCN.
    """
    return distributedcontrolnode.get_dcn()

# Rota para obter interfaces Ethernet
@app.route(f'/redfish/v1/Systems/{system_id}/EthernetInterfaces', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EthernetInterfaceCollection")
def get_computersystem_id_ethernetInterfaces():
    """ Rota para obter interfaces Ethernet

    Returns:
        return: Retorna todas as interfaces dentro do JSON de EthernetInterfaces.
    """
    return ethernetinterfaces.get_computersystem_id_ethernetInterfaces()

# Rota para obter informações detalhadas de uma interface Ethernet específica
@app.route(f'/redfish/v1/Systems/{system_id}/EthernetInterfaces/<iface>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EthernetInterface")
def get_computersystem_id_ethernetInterfaces_iface(iface):
    """
    Permite obter informações detalhadas de uma interface Ethernet específica.

    Args:
        iface (str): Nome da interface Ethernet.

    Returns:
        response: Retorna o JSON detalhado da interface Ethernet solicitada.
                  Retorna 404 se a interface não for encontrada.
    """
    funcs = ethernetinterfaces.dynamic_eth_funcs() # Obtém funções dinâmicas de interfaces Ethernet
    # Itera sobre as funções dinâmicas de interfaces Ethernet
    # Se o nome da função corresponder ao parâmetro iface, chama a função
    for func in funcs:
        if func.__name__ == iface:
            return func()
    abort(404)

# Permite obter e atualizar informações do serviço de eventos
@app.route('/redfish/v1/EventService', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EventService")
def event_service():
    """
    Permite obter e atualizar informações do serviço de eventos.

    Returns:
        response: 
            - GET: Retorna o JSON do serviço de eventos.
            - PATCH: Atualiza configurações do serviço de eventos e retorna mensagem de sucesso ou erro.
    """
    if request.method == 'GET':
        return Response( # Obtém o serviço de eventos
            json.dumps(eventservice.get_event_service(), indent=2), # Formata o JSON
            mimetype='application/json'
        )
    elif request.method == 'PATCH': # Atualiza o serviço de eventos
        # Verifica se o serviço de eventos está habilitado
        data = request.get_json()
        response = {}
        # Atualiza os campos do serviço de eventos conforme os dados recebidos
        if "DeliveryRetryAttempts" in data:
            readings.set_delivery_retry_attempts(data["DeliveryRetryAttempts"])
            response["DeliveryRetryAttempts"] = data["DeliveryRetryAttempts"]

        if "DeliveryRetryIntervalSeconds" in data:
            readings.set_delivery_retry_interval_seconds(data["DeliveryRetryIntervalSeconds"])
            response["DeliveryRetryIntervalSeconds"] = data["DeliveryRetryIntervalSeconds"]

        if "ServiceEnabled" in data:
            readings.set_service_enabled(data["ServiceEnabled"])
            response["ServiceEnabled"] = data["ServiceEnabled"]

        if response:
            return jsonify({
                "Message": "Configurações atualizadas com sucesso!",
                **response
            }), 200
        else:
            return jsonify({"Message": "Nenhum campo válido foi fornecido"}), 400

# Permite obter e criar assinaturas de eventos
@app.route('/redfish/v1/EventService/Subscriptions', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EventDestinationCollection")
def event_subscriptions_collection():
    """
    Permite obter e criar assinaturas de eventos.

    Returns:
        response:
            - GET: Retorna todas as assinaturas de eventos.
            - POST: Cria uma nova assinatura de evento.
    """
    if request.method == 'GET':
        return eventdestination.get_event_subscriptions()
    elif request.method == 'POST':
        return eventdestination.create_event_subscription()

# Permite obter e excluir assinaturas de eventos
@app.route('/redfish/v1/EventService/Subscriptions/<subscription_id>', methods=['GET', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EventDestination")
def event_subscription_detail(subscription_id):
    """
    Permite obter e excluir uma assinatura de evento específica.

    Args:
        subscription_id (str): ID da assinatura de evento.

    Returns:
        response:
            - GET: Retorna detalhes da assinatura.
            - DELETE: Exclui a assinatura.
    """
    if request.method == 'GET':
        return eventdestination.get_event_subscription(subscription_id)
    elif request.method == 'DELETE':
        return eventdestination.delete_event_subscription(subscription_id)

# Permite enviar um evento de teste
@app.route('/redfish/v1/EventService/Actions/EventService.SubmitTestEvent', methods=['POST'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("EventService")
def submit_test_event():
    """
    Permite enviar um evento de teste para o serviço de eventos.

    Returns:
        response: Resultado do envio do evento de teste.
    """
    return eventservice.submit_test_event()

# Retorna informações sobre os gerenciadores disponíveis
@app.route('/redfish/v1/Managers', methods=['GET'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ManagerCollection")
def managers():
    """
    Retorna informações sobre os gerenciadores disponíveis.

    Returns:
        response: JSON com a lista de gerenciadores disponíveis.
    """
    return manager.get_managers()

# Permite obter e atualizar informações de um gerenciador específico
@app.route('/redfish/v1/Managers/<manager_id>', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Manager")
def manager_details(manager_id):
    """
    Permite obter e atualizar informações de um gerenciador específico.

    Args:
        manager_id (str): ID do gerenciador.

    Returns:
        response: 
            - GET: Retorna detalhes do gerenciador.
            - PATCH: Atualiza informações do gerenciador.
    """
    if request.method == 'GET':
        return manager.get_manager_details(manager_id)
    elif request.method == 'PATCH':
        return manager.update_manager(manager_id)

# Permite obter e atualizar informações do protocolo de rede de um gerenciador específico
@app.route('/redfish/v1/Managers/<manager_id>/NetworkProtocol', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("ManagerNetworkProtocol")
def network_protocol(manager_id):
    """
    Permite obter e atualizar informações do protocolo de rede de um gerenciador específico.

    Args:
        manager_id (str): ID do gerenciador.

    Returns:
        response: 
            - GET: Retorna informações do protocolo de rede.
            - PATCH: Atualiza informações do protocolo de rede.
    """
    if request.method == 'GET':
        return manager.get_manager_network_protocol()
    elif request.method == 'PATCH':
        return manager.update_network_protocol()

# Permite obter e atualizar informações de contas de gerenciador
@app.route('/redfish/v1/SessionService', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("SessionService")
def session_service():
    """
    Permite obter e atualizar informações do serviço de sessão.

    Returns:
        response: 
            - GET: Retorna informações do serviço de sessão.
            - PATCH: Atualiza informações do serviço de sessão.
    """
    if request.method == 'GET':
        return sessionservice.get_session_service()
    elif request.method == 'PATCH':
        return sessionservice.update_session_service(request.json)

# Permite obter e criar sessões
@app.route('/redfish/v1/SessionService/Sessions', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
def session_collection():
    """
    Permite obter e criar sessões.

    Returns:
        response: 
            - GET: Retorna todas as sessões.
            - POST: Cria uma nova sessão.
            - OPTIONS: Responde a requisições CORS preflight.
    """
    session_service_state = sessionservice.load_session_service() # Carrega o estado do serviço de sessão
    # Verifica se o serviço de sessão está habilitado

    # Trata requisição CORS preflight (OPTIONS)
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200

    if not session_service_state["ServiceEnabled"]:
        return make_response({"error": "SessionService is disabled."}, 403)

    if request.method == 'GET':
        return session.get_sessions()
    elif request.method == 'POST':
        return session.create_session()

# Permite obter e excluir uma sessão específica
@app.route('/redfish/v1/SessionService/Sessions/<session_id>', methods=['GET', 'DELETE'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("Session")
def session_detail(session_id):
    """
    Permite obter e excluir uma sessão específica.

    Args:
        session_id (str): ID da sessão.

    Returns:
        response: 
            - GET: Retorna detalhes da sessão.
            - DELETE: Exclui a sessão.
    """
    session_service_state = sessionservice.load_session_service()

    if not session_service_state["ServiceEnabled"]:
        return make_response({"error": "SessionService is disabled."}, 403)

    if request.method == 'GET':
        return session.get_session(session_id)
    elif request.method == 'DELETE':
        return session.delete_session(session_id)

# Permite obter e atualizar informações do serviço de atualização
@app.route('/redfish/v1/UpdateService', methods=['GET', 'PATCH'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("UpdateService")
def update_service():
    """
    Permite obter e atualizar informações do serviço de atualização.

    Returns:
        response: 
            - GET: Retorna informações do serviço de atualização.
            - PATCH: Atualiza informações do serviço de atualização.
    """
    if request.method == 'GET':
        return updateservice.get_update_service()
    elif request.method == 'PATCH':
        return updateservice.update_update_service(request.json)

# Permite realizar uma atualização simples
@app.route('/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate', methods=['POST'], strict_slashes=False) 
@conditional_limit(RATE_LIMIT)                      # Limita a 1 requisição por segundo
@requires_authentication
@requires_privilege("UpdateService")
def update_firmware():
    """
    Permite realizar uma atualização simples de firmware.

    Returns:
        response: Resultado da atualização.
    """
    return updateservice.simple_update()

# Função para limpar sessões expiradas
# Remove sessões cujo tempo de expiração já passou
def limpar_sessoes_expiradas():
    """
    Remove sessões expiradas do armazenamento de sessões.

    Esta função percorre todas as sessões salvas, verifica se o tempo de expiração já passou
    e remove as sessões expiradas. As sessões atualizadas são salvas novamente.

    Side Effects:
        Remove sessões expiradas do arquivo de sessões e imprime no console as sessões removidas.
    """
    sessions = load_sessions() # Carrega as sessões
    current_time = time.time() # Obtém o tempo atual
    expired = [sid for sid, sess in sessions.items() if sess["ExpirationTime"] < current_time] # Filtra sessões expiradas
    # Se houver sessões expiradas, remove-as e salva as sessões atualizadas
    if expired:
        print(f"Limpando sessões expiradas: {expired}")
        for sid in expired:
            del sessions[sid]
        save_sessions(sessions)

# Função para iniciar o servidor Flask
# Configura o agendador para limpar sessões expiradas a cada 2 minutos e inicia o servidor Flask com HTTPS
def iniciar_servidor_flask():
    """
    Inicia o servidor Flask com HTTPS e agenda a limpeza periódica de sessões expiradas.

    - Limpa sessões expiradas antes de iniciar o servidor.
    - Agenda a limpeza de sessões a cada 2 minutos usando APScheduler.
    - Garante que o agendador será parado ao encerrar o programa.
    - Inicia o servidor Flask com o contexto SSL configurado.

    Side Effects:
        Inicia o servidor Flask e o agendador de tarefas em background.
    """
    # Antes de iniciar o servidor, já limpa as sessões expiradas
    limpar_sessoes_expiradas()

    # Inicia o agendador para continuar limpando a cada 2 minutos
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=limpar_sessoes_expiradas, trigger="interval", seconds=120)
    scheduler.start()

    # Garante que o scheduler será parado ao encerrar o programa
    atexit.register(lambda: scheduler.shutdown())

    # Inicia o servidor Flask com HTTPS
    app.run(host=FLASK_IP, port=FLASK_PORT, ssl_context=(CERT_FILE, KEY_FILE))
    

# Configuração de CORS para permitir requisições de um domínio específico
@app.after_request
def add_cors_headers(response):
    """
    Adiciona cabeçalhos CORS à resposta HTTP.

    Args:
        response: Objeto de resposta do Flask.

    Returns:
        response: Objeto de resposta com cabeçalhos CORS adicionados.
    """
    response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5000'  # ou '*', se estiver testando
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

def get_authenticated_username():
    # Tenta obter pelo token de sessão
    token = request.headers.get("X-Auth-Token")
    sessions = load_sessions()
    for sess in sessions.values():
        if sess.get("Token") == token:
            return sess.get("UserName")
    # Tenta obter pelo Authorization Basic
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64
        try:
            decoded = base64.b64decode(auth_header.split()[1]).decode()
            username, _ = decoded.split(":", 1)
            return username
        except Exception:
            pass
    return "anonymous"

@app.after_request
def log_all_requests(response):
    try:
        username = get_authenticated_username()
        endpoint = request.path
        method = request.method
        status = response.status_code
        if status != 404:
            add_audit_log_entry(
                system_id=readings.machine_id(),
                logservice_id="Log1",
                message=f"{method} {endpoint} - Status {status}",
                user_name=username,
                severity="OK" if status < 400 else "Warning",
                message_id=f"HTTP.{method}.{status}"
            )
    except Exception:
        pass
    return response 

# Função para gerar certificados interativos
# Solicita ao usuário o Common Name (CN) e gera os certificados necessários
# O CN é usado para identificar o certificado e deve ser único
# O certificado gerado é válido por 365 dias
# O arquivo de extensão (domain.ext) é criado para incluir o SAN (Subject Alternative Name)
# O SAN é usado para especificar os nomes alternativos do certificado
# O certificado gerado é salvo como domainSAN.crt
# O arquivo de chave privada é salvo como domain.key
# O arquivo CSR (Certificate Signing Request) é salvo como domain.csr
# O arquivo de extensão é salvo como domain.ext
# O certificado gerado é assinado com a chave privada
def gerar_certificados_interativo():
    """
    Gera certificados SSL interativamente solicitando o Common Name (CN) ao usuário.

    - Gera chave privada, CSR, arquivo de extensão e certificado com SAN.
    - Salva os arquivos gerados no diretório atual.

    Side Effects:
        Cria arquivos de certificado, chave privada, CSR e extensão no disco.
        Imprime mensagens de status no console.
    """
    cn = input("Digite o Common Name (CN) para o certificado: ").strip()

    if not cn:
        print(" CN não pode estar vazio.")
        return

    # Criação de arquivos
    key_file = "domain.key"
    csr_file = "domain.csr"
    ext_file = "domain.ext"
    cert_file = "domainSAN.crt"

    print(" Gerando chave privada...")
    subprocess.run(["openssl", "genrsa", "-out", key_file, "2048"], check=True)

    print(" Gerando CSR...")
    subprocess.run([
        "openssl", "req", "-new", "-key", key_file,
        "-out", csr_file,
        "-subj", f"/CN={cn}"
    ], check=True)

    print(" Criando arquivo domain.ext com SAN...")
    with open(ext_file, "w") as f:
        f.write(f"subjectAltName=DNS:{cn}\n")

    print(" Gerando certificado com SAN...")
    subprocess.run([
        "openssl", "x509", "-req", "-days", "365",
        "-in", csr_file,
        "-signkey", key_file,
        "-out", cert_file,
        "-extfile", ext_file
    ], check=True)

    print(" Certificado gerado com sucesso:", cert_file)



#USAR ssl_context = "adhoc" para testar HTTPS localmente sem se preocupar em gerar e configurar certificados

# Função principal
# Configura certificados SSL, inicia o servidor Flask e o processo de descoberta SSDP
if __name__ == '__main__': 
    """
    Bloco principal de inicialização do servidor RedfishPi.

    
    - Obtém o IP local da máquina.
    - Verifica se os certificados SSL estão atualizados para o IP atual.
      - Se não estiverem, gera novos certificados e registra no sistema.
    - Inicia o servidor Flask em um processo separado, usando HTTPS.
    - Inicia o processo de descoberta SSDP em paralelo para anunciar o serviço na rede.
    - Aguarda o término dos processos Flask e SSDP.

    Side Effects:
        - Gera e registra certificados SSL se necessário.
        - Inicia processos paralelos para o servidor Flask e descoberta SSDP.
        - O servidor Flask ficará disponível no IP e porta configurados via HTTPS.
    """
    # Inicia o servidor Flask em um processo separado 

    ip = obter_ip_local() # Obtém o IP local
    if not certificados_estao_atualizados(ip):
        gerar_certificados(ip)
        if os.getenv("REGISTER_CERT_IN_SYSTEM", "false").lower() == "true":
         registrar_certificado_no_sistema()

    ssdp_control.start_ssdp()

    # Inicia o servidor Flask em um processo separado
    # O processo Flask é iniciado com o IP e porta configurados
    processo_flask = Process(target=iniciar_servidor_flask) 
    processo_flask.start() 

    # Inicia o processo de descoberta SSDP em um processo separado
    # O processo SSDP é iniciado para descobrir dispositivos na rede
    #processo_ssdp = Process(target=discovery_SSDP) 
    #processo_ssdp.start() 
    
    # Aguarda o término dos processos
    processo_flask.join() 
    #processo_ssdp.join()