# Arquitetura do sistema

A API segue uma organização simples em camadas lógicas:

- **API (`principal.py`)**: recebe HTTP, valida entradas e monta respostas.
- **Schemas (`esquemas.py`)**: define o formato e a validação dos dados.
- **Modelos (`modelos.py`)**: representa entidades persistidas.
- **Segurança (`seguranca.py`)**: valida JWT, hash de senhas e perfis.
- **Banco (`banco_de_dados.py`)**: cria engine e sessões do SQLAlchemy.

```mermaid
flowchart TD
    Cliente[Cliente / Totem / Balcão / Web] --> API[FastAPI REST]
    API --> Auth[JWT e controle de perfil]
    API --> Regras[Regras de negócio]
    Regras --> ORM[SQLAlchemy]
    ORM --> DB[(PostgreSQL ou SQLite)]
    Regras --> Audit[Auditoria]
    Regras --> Mock[Pagamento simulado]
```

## Fluxo principal do pedido

```mermaid
sequenceDiagram
    actor C as Cliente
    participant API as FastAPI
    participant DB as Banco
    participant PG as Pagamento mock
    C->>API: POST /api/pedidos
    API->>DB: valida unidade, produtos e estoque
    API->>DB: registra pedido e reserva estoque
    API-->>C: pedido aguardando pagamento
    C->>API: POST /api/pedidos/{id}/pagamento
    API->>PG: simula aprovação/recusa
    PG-->>API: resultado
    alt aprovado
        API->>DB: atualiza status e pontos
    else recusado
        API->>DB: cancela pedido e devolve estoque
    end
    API-->>C: resultado do pagamento
```
