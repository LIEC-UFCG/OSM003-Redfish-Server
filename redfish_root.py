import readings

def get_redfish_v1():
    """
    Returns the Redfish v1 ServiceRoot in Redfish format.

    The ServiceRoot is the main entry point of the Redfish API,
    providing links to the service's primary resources.

    Returns:
        dict: Dictionary with ServiceRoot data, including links to
        AccountService, Chassis, Systems, Managers, SessionService,
        EventService, JsonSchemas, and UpdateService.
    """
    redfish_v1 = {
        "@odata.context": "/redfish/v1/$metadata#ServiceRoot.ServiceRoot",
        "@odata.type": "#ServiceRoot.v1_17_0.ServiceRoot",
        "RedfishVersion": "1.15.0",
        "@odata.id": "/redfish/v1/",
        "Id": "RootService",
        "Name": "Root Service",
        #"RedfishVersion": "1.0.0",
        "UUID": readings.system_uuid(), 
        "AccountService": {
            "@odata.id": "/redfish/v1/AccountService"
        },
        "Chassis": {
            "@odata.id": "/redfish/v1/Chassis"
        },
        "Systems":{                                         
            "@odata.id": "/redfish/v1/Systems"
        },
        #"DistributedControlNode": {                                
        #    "@odata.id": "/redfish/v1/DistributedControlNode"
        #},
        "EventService":{
            "@odata.id": "/redfish/v1/EventService"
        },
        #"EthernetInterfaces":{
        #    "@odata.id": "/redfish/v1/Systems/" + readings.machine_id() + "/EthernetInterfaces"
        #},
        "JsonSchemas": {
            "@odata.id": "/redfish/v1/JsonSchemas"
        },
        "Managers":{
            "@odata.id": "/redfish/v1/Managers"
        },
        "SessionService": {
            "@odata.id":  "/redfish/v1/SessionService"
        },
        "Systems":{                                          
            "@odata.id": "/redfish/v1/Systems"
        },
        "UpdateService": {                                          # REVIEW
            "@odata.id":  "/redfish/v1/UpdateService"
        },
        "Links": {
            "Sessions": {
                "@odata.id": "/redfish/v1/SessionService/Sessions"
            }
        }
    }
    return redfish_v1
