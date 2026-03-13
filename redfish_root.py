import readings

def get_redfish_v1():
    """
    Retorna o ServiceRoot do Redfish v1 no formato Redfish.

    O ServiceRoot é o ponto de entrada principal da API Redfish, fornecendo links para os principais recursos do serviço.

    Returns:
        dict: Dicionário com os dados do ServiceRoot, incluindo links para AccountService, Chassis, Systems, Managers, SessionService, EventService, JsonSchemas e UpdateService.
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
        "Links": {
            "Sessions": {
                "@odata.id": "/redfish/v1/SessionService/Sessions"
            },
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
        "UpdateService": {                                          # REVISAR
            "@odata.id":  "/redfish/v1/UpdateService"
        }
    }
    return redfish_v1
