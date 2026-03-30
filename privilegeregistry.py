from flask import jsonify

def priv():    
    """
    Returns the Privilege Registry in Redfish format.

    The Privilege Registry describes the mapping of privileges required to access and operate
    on different entities and operations of the Redfish API, according to DMTF specification.

    Returns:
        flask.Response: JSON response with the Privilege Registry, including entities, operations and associated privileges.
    """
    response = {
            "@odata.type": "#PrivilegeRegistry.v1_1_4.PrivilegeRegistry",
            "Id": "Redfish_1.0.1_PrivilegeRegistry",
            "Name": "Privilege Map",
            "PrivilegesUsed": [
                "Login",
                "ConfigureManager",
                "ConfigureUsers",
                "ConfigureComponents",
                "ConfigureSelf"
            ],
            "OEMPrivilegesUsed": [],
            "Mappings": 
            [  
                {
                    "Entity": "AccountService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Chassis",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ChassisCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ComputerSystem",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ComputerSystemCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "EthernetInterface",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    },
                    "SubordinateOverrides": [
                        {
                            "Targets": [
                                "Manager",
                                "EthernetInterfaceCollection"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureManager"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureManager"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureManager"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureManager"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "EthernetInterfaceCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "EventDestination",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "EventDestinationCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "EventService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "JsonSchemaFile",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "JsonSchemaFileCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "LogEntry",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    },
                    "SubordinateOverrides": [
                        {
                            "Targets": [
                                "ComputerSystem",
                                "LogServiceCollection",
                                "LogService",
                                "LogEntryCollection"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "Targets": [
                                "Chassis",
                                "LogServiceCollection",
                                "LogService",
                                "LogEntryCollection"
                            ],
                            "OperationMap": {
                                "GET": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "HEAD": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "LogEntryCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    },
                    "SubordinateOverrides": [
                        {
                            "Targets": [
                                "ComputerSystem",
                                "LogServiceCollection",
                                "LogService"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "Targets": [
                                "Chassis",
                                "LogServiceCollection",
                                "LogService"
                            ],
                            "OperationMap": {
                                "GET": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "HEAD": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "LogService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    },
                    "SubordinateOverrides": [
                        {
                            "Targets": [
                                "ComputerSystem",
                                "LogServiceCollection"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "Targets": [
                                "Chassis",
                                "LogServiceCollection"
                            ],
                            "OperationMap": {
                                "GET": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "HEAD": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "LogServiceCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    },
                    "SubordinateOverrides": [
                        {
                            "Targets": [
                                "ComputerSystem"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "Targets": [
                                "Chassis"
                            ],
                            "OperationMap": {
                                "GET": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "HEAD": [
                                    {
                                        "Privilege": [
                                            "Login"
                                        ]
                                    }
                                ],
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "PUT": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "DELETE": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ],
                                "POST": [
                                    {
                                        "Privilege": [
                                            "ConfigureComponents"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "Manager",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ManagerCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ManagerAccount",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ]
                    },
                    "PropertyOverrides": [
                        {
                            "Targets": [
                                "Password"
                            ],
                            "OperationMap": {
                                "PATCH": [
                                    {
                                        "Privilege": [
                                            "ConfigureUsers"
                                        ]
                                    },
                                    {
                                        "Privilege": [
                                            "ConfigureSelf"
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "Entity": "ManagerAccountCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureUsers"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ManagerNetworkProtocol",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Memory",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "MemoryCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "MemoryMetrics",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkAdapter",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkAdapterCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkAdapterMetrics",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkInterface",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkInterfaceCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkPort",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "NetworkPortCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "OperatingConfig",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "OperatingConfigCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "PowerSubsystem",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "PowerSupply",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "PowerSupplyCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "PowerSupplyMetrics",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Processor",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ProcessorCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ProcessorMetrics",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Role",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "RoleCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SecureBoot",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Sensor",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SensorCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ServiceRoot",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            },
                            {
                                "Privilege": [
                                    "NoAuth"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            },
                            {
                                "Privilege": [
                                    "NoAuth"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Session",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            },
                            {
                                "Privilege": [
                                    "ConfigureSelf"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SessionCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SessionService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SimpleStorage",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "SimpleStorageCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Storage",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "StorageCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Task",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "TaskCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "TaskService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Thermal",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ThermalMetrics",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "ThermalSubsystem",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureManager"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "UpdateService",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "Volume",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
                {
                    "Entity": "VolumeCollection",
                    "OperationMap": {
                        "GET": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "HEAD": [
                            {
                                "Privilege": [
                                    "Login"
                                ]
                            }
                        ],
                        "PATCH": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "POST": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "PUT": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ],
                        "DELETE": [
                            {
                                "Privilege": [
                                    "ConfigureComponents"
                                ]
                            }
                        ]
                    }
                },
            ]
    }
    return jsonify(response)
