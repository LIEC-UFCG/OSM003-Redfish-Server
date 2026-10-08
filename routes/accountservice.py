from flask import Blueprint, request, jsonify
import logging

from extensions import conditional_limit
from auth import requires_authentication, requires_privilege
from config import RATE_LIMIT
from logservice import add_audit_log_entry
import accountservice
import manageraccount
import roles
import readings

account_service_bp = Blueprint(
    "account_service", __name__, url_prefix="/redfish/v1/AccountService"
)

system_id = readings.machine_id()

# Route for /redfish/v1/AccountService/ endpoint, allows GET and PATCH methods
@account_service_bp.route('', methods=['GET', 'PATCH'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                     # Limit to 1 request per second
@requires_authentication
@requires_privilege("AccountService")
def account_service():
    """
    Route for /redfish/v1/AccountService/ endpoint.

    Allow GET to retrieve or PATCH to update AccountService information.

    Returns:
        flask.Response: 
            - GET: Returns AccountService data.
            - PATCH: Updates AccountService state and returns success or error message.
    """
    if request.method == 'GET':
        return accountservice.get_account_service()
    elif request.method == 'PATCH':
        return accountservice.update_account_service(request.json)

# Route for /redfish/v1/AccountService/Accounts endpoint, allows GET and POST methods
@account_service_bp.route('/Accounts', methods=['GET', 'POST'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("ManagerAccountCollection")
def accounts_collection():
    """
    Route for /redfish/v1/AccountService/Accounts endpoint.

    Allow GET to retrieve account list or POST to create a new account.

    Returns:
        flask.Response:
            - GET: Returns list of accounts.
            - POST: Returns newly created account.
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

# Route for /redfish/v1/AccountService/Accounts/<account_id> endpoint, allows GET, PATCH and DELETE methods
@account_service_bp.route('/Accounts/<account_id>', methods=['GET', 'PATCH', 'DELETE'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("ManagerAccount")
def account_detail(account_id):
    """
    Route for /redfish/v1/AccountService/Accounts/<account_id> endpoint.

    Allow GET to retrieve, PATCH to update, or DELETE to remove a specific account.

    Args:
        account_id (str): Account ID.

    Returns:
        flask.Response:
            - GET: Returns account data.
            - PATCH: Updates account.
            - DELETE: Removes account.
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

# Route for /redfish/v1/AccountService/Roles endpoint, returns available roles
@account_service_bp.route('/Roles', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("RoleCollection")
def roles_collection():
    """
    Route for /redfish/v1/AccountService/Roles endpoint.

    Returns list of available roles (roles).

    Returns:
        flask.Response: List of available roles.
    """
    return roles.get_roles()

# Route for /redfish/v1/AccountService/Roles/<role_id> endpoint, returns details of specific role
@account_service_bp.route('/Roles/<role_id>', methods=['GET'], strict_slashes=False)
@conditional_limit(RATE_LIMIT)                      # Limit to 1 request per second
@requires_authentication
@requires_privilege("Role")
def role_detail(role_id):
    """
    Route for /redfish/v1/AccountService/Roles/<role_id> endpoint.

    Returns details of a specific role (role).

    Args:
        role_id (str): Role ID.

    Returns:
        flask.Response: Details of requested role.
    """
    return roles.get_role(role_id)