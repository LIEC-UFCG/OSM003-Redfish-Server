from flask import jsonify

def get_json_schemas():
    """
    Retorna a coleção de JSON Schemas disponíveis no serviço Redfish.

    Returns:
        flask.Response: Resposta JSON com a coleção de schemas disponíveis, incluindo links para cada schema.
    """
    schema_collection = {
        "@odata.context": "/redfish/v1/$metadata#JsonSchemaFile.JsonSchemaFile",
        "@odata.id": "/redfish/v1/JsonSchemas",
        "@odata.type": "#JsonSchemaFileCollection.JsonSchemaFileCollection",
        "Name": "JSON Schema Collection",
        "Members": [
            {
                "@odata.id": "/redfish/v1/JsonSchemas/Chassis.v1_26_0"
            }
        ],
        "Members@odata.count": 1
    }
    return jsonify(schema_collection)

def get_chassis_schemas():
    """
    Retorna o JSON Schema específico do recurso Chassis.

    Returns:
        flask.Response: Resposta JSON com o schema do Chassis, incluindo localização e metadados.
    """
    schema_chassis = {
        "@odata.type": "#JsonSchemaFile.v1_1_5.JsonSchemaFile",
        "Id": "Chassis.v1_26_0",
        "Name": "Chassis Schema File",
        "Description": "Chassis Schema File Location",
        "Languages": ["en"],
        "Schema": "#Chassis.v1_26_0.Chassis",
        "Location": [
            {
                "Language": "en",
                "ArchiveUri": "/Schemas.gz",
                "PublicationUri": "http://redfish.dmtf.org/schemas/v1/Chassis.v1_26_0.json",
                "ArchiveFile": "Chassis.v1_26_0.json"
            }
        ],
        "@odata.id": "/redfish/v1/JsonSchemas/Chassis.v1_26_0"
    }
    return jsonify(schema_chassis)