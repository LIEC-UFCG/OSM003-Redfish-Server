from flask import jsonify

def get_json_schemas():
    """
    Returns the collection of available JSON Schemas in the Redfish service.

    Returns:
        flask.Response: JSON response with the available schemas collection, including links for each schema.
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
    Returns the specific JSON Schema for the Chassis resource.

    Returns:
        flask.Response: JSON response with Chassis schema, including location and metadata.
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