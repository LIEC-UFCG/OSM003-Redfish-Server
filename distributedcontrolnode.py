def get_dcn():
    """
    Retorna informações do Distributed Control Node (DCN) no formato Redfish.

    Returns:
        dict: Dicionário com os dados do DCN, incluindo tipo, compatibilidade O-PAS e status.
    """
    dcn = {
        "@odata.type": "#DistributedControlNode.v1_0_0.DistributedControlNode",
        "@odata.id": "/redfish/v1/DistributedControlNode",
        "Id": "DistributedControlNode",
        "Name": "Distributed Control Node",
        "NodeType": "DCN",  # Tipo de nó O-PAS, pode ser "DCN" ou outro
        "OPASCompatibility": {
            "OPASCertificationStatus": "Unknown",  # Se implementado, status da certificação O-PAS para esse profile
            "OPASOptionalFeatureList": [  # List of IfImplemented and Recommended resources and properties supported
                "Unknown",
                "Unknown"
            ],
            "OPASProfile": "OSM-003",  # Nome do perfil O-PAS compatível, se implementado
            "OPASVersion": "2.1"  # Versão do perfil O-PAS, se implementado
        }
    }
    return dcn