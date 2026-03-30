import json
import os
from flask import jsonify, request, make_response

# File name where AccountService state will be saved
ACCOUNT_SERVICE_FILE = "account_service.json"



# Default initial state with only required fields
default_account_service_state = {
    "ServiceEnabled": True,
    "Accounts": "/redfish/v1/AccountService/Accounts",
    "MinPasswordLength": 8,
    "MaxPasswordLength": 32,
    "AccountLockoutThreshold": 5,
    "AccountLockoutDuration": 600,  # 10 minutes
    "AccountLockoutCounterResetAfter": 300,  # 5 minutes
    "AccountLockoutCounterResetEnabled": True,
}

# Function to load AccountService state from JSON file
def load_account_service():
    """Load AccountService state from JSON file.
    
    Returns:
        dict: Current AccountService state. If file doesn't exist, returns default state.
    """
    if os.path.exists(ACCOUNT_SERVICE_FILE):            # Check if file exists
        with open(ACCOUNT_SERVICE_FILE, "r") as file:
            return json.load(file)                      # Load state from JSON file
    return default_account_service_state.copy()         # Return copy of default state

# Function to save AccountService state to JSON file
def save_account_service(state):
    """Save AccountService state to JSON file.
    
    Args:
        state (dict): AccountService state to be saved.
    """
    with open(ACCOUNT_SERVICE_FILE, "w") as file:
        json.dump(state, file, indent=4)

# Initialize AccountService state when loading module
account_service_state = load_account_service()

# Function to get AccountService data
def get_account_service():
    """Return AccountService data in Redfish format.
    
    Returns:
        flask.Response: JSON response with AccountService data.
    """
    response = {
        "@odata.id": "/redfish/v1/AccountService",
        "@odata.type": "#AccountService.v1_17_0.AccountService",
        "Id": "AccountService",
        "Name": "Account Service",
        "Description": "Local Manager Account Service",
        "ServiceEnabled": account_service_state["ServiceEnabled"],
        "Accounts": {
            "@odata.id": account_service_state["Accounts"]
        },
        "Roles": {
            "@odata.id": "/redfish/v1/AccountService/Roles"
        },
        "MinPasswordLength": account_service_state["MinPasswordLength"],
        "MaxPasswordLength": account_service_state["MaxPasswordLength"]
    }
    return jsonify(response)

# Function to update AccountService state
def update_account_service(data):
    """Update only the 'ServiceEnabled' required field of AccountService.
    
    Args:
        data (dict): Dictionary containing 'ServiceEnabled' field to be updated.
    
    Returns:
        flask.Response: Success or error message.
    """
    if "ServiceEnabled" in data:        # Check if 'ServiceEnabled' field is present in data
        account_service_state["ServiceEnabled"] = bool(data["ServiceEnabled"])  # Update state
        save_account_service(account_service_state)     # Save updated state to file
        return make_response({"message": "AccountService updated successfully."}, 200)      # Return success
        
        # Return error if provided data is not valid
    return make_response({"error": "Invalid properties in request."}, 400)
  
# Function to authenticate a user
def authenticate(username, password):
    """Check if user and password are valid.
    
    Args:
        username (str): User name.
        password (str): User password.
    
    Returns:
        bool: True if credentials are valid, False otherwise.
    """
    accounts = load_account_service()["Users"]      # Load list of users from AccountService state
    for user in accounts:       # Iterate over users
        if user["UserName"] == username and user["Password"] == password:       # Check if username and password match
            return True  # Return True if credentials are valid
    return False        # Return False if credentials are invalid

