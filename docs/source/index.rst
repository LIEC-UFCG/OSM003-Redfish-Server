.. RedfishServer documentation master file, created by
   sphinx-quickstart on Thu May 22 12:06:25 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RedfishServer documentation
===========================

Este documento apresenta a documentação técnica do projeto de desenvolvimento de um servidor Redfish personalizado. Ele tem como objetivo descrever a arquitetura, funcionamento, endpoints implementados e comportamento da API desenvolvida para exposição de métricas de sistemas embarcados ou computadores industriais, seguindo a especificação Redfish da DMTF e o perfil O-PAS OSM-003.

A documentação foi gerada automaticamente com auxílio da ferramenta **Sphinx**, a partir de docstrings e comentários estruturados no código Python. Ela visa facilitar a compreensão, manutenção, expansão e testes do sistema por desenvolvedores, mantenedores e avaliadores técnicos.

Estrutura do Documento
======================

A documentação está dividida em seções principais que refletem a organização do código-fonte:

- **Introdução**: Explica o objetivo do projeto e os padrões seguidos (Redfish, O-PAS).
- **Módulo principal (main.py)**: Descreve os endpoints REST definidos usando Flask, como são roteados e como se relacionam com o modelo Redfish.
- **Coleta de Métricas (readings.py)**: Explica as funções responsáveis por capturar e formatar os dados do sistema operacional e hardware (temperatura, memória, CPU, sessões, processos, interfaces de rede, armazenamento, etc).
- **Implementações de Coleções**: Mostra os arquivos que constroem os recursos Redfish de forma modular (como Managers, Systems, Chassis, etc).
- **Autenticação e Sessões**: Detalha como o servidor implementa autenticação via Redfish, controle de sessões e tokens (X-Auth-Token).
- **Configurações e Persistência**: Explica como informações como hora do sistema, asset tags e status de serviços são armazenados em arquivos JSON.

Hierarquia da Documentação
==========================

A hierarquia dos endpoints do servidor segue o padrão Redfish, que é estruturado de forma semelhante a um sistema de arquivos, com recursos principais e sub-recursos. Abaixo está um resumo da hierarquia dos principais endpoints, baseada no seu arquivo **main.py**:

::

    /redfish/v1/
    ├── AccountService/
    │   └── Roles/
    │       └── <role_id>
    │   └── Accounts/
    │       └── <account_id>
    ├── Chassis/
    │   └── <machine_id>/
    │       ├── ThermalSubsystem/
    │           └── ThermalMetrics
    │       ├── PowerSubsystem/
    │       ├── Sensors/
    ├── DistributedControlNode/
    ├── EventService/
    │   └── Subscriptions/
    │       ├── <subscriptions_id>/
    ├── JsonSchemas/
    │   └── <JsonSchemaField>
    ├── Managers/
    │   └── <manager_id>/
    │       └── NetworkProtocol/
    ├── SessionService/
    │   └── Sessions/
    │       └── <session_id>/
    ├── Systems/
    │   ├── <machine_id>/
    │   │   ├── Memory/
    │   │   ├── Processors/
    │           └── ProcessorId
    │   │   ├── SimpleStorage/
    │           └── SimpleStorageId
    │   │   ├── OperatingSystem/
    │           └── OperatingSystemMetrics
    │           └── Containers/
    │               └── <container_id>/
    │   │   └── EthernetInterfaces/
    │           └── <interface_id>/
    │   │   └── LogServices/
    │           └── <log_id>
    │               └── Entries/
    │                   └── <event_id>/
    └── UpdateService/

Cada uma dessas entradas corresponde a um endpoint implementado via Flask e mapeado por funções que extraem dados reais do sistema. A documentação segue essa organização, permitindo ao leitor navegar da estrutura geral do Redfish até as funções que populam os dados de cada recurso.

Considerações Finais
====================

A documentação serve como base para futuros desenvolvimentos, validações e testes de conformidade com Redfish. A estrutura modular e os comentários detalhados visam garantir facilidade de manutenção e adaptação.

---

.. toctree::
   :maxdepth: 2
   :caption: Principal

   main
   config
   modules
   service_discovery
   readings

.. toctree::
   :maxdepth: 2
   :caption: Autenticação e Sessões

   auth
   session
   sessionservice
   roles
   manager
   manageraccount

.. toctree::
   :maxdepth: 2
   :caption: Serviços Redfish

   redfish_root

.. toctree::
   :maxdepth: 2
   :caption: Gerenciamento de Sistemas

   accountservice
   chassis
   computersystem
   operatingsystem
   updateservice

.. toctree::
   :maxdepth: 2
   :caption: Containers e Recursos

   container
   ethernetinterfaces
   distributedcontrolnode
   jsonschemas

.. toctree::
   :maxdepth: 2
   :caption: Logs e Eventos

   eventservice
   eventdestination
   logentry
   logservice