# DER conceitual

```mermaid
erDiagram
    USUARIO ||--o{ PEDIDO : realiza
    UNIDADE ||--o{ PEDIDO : recebe
    PEDIDO ||--|{ ITEM_PEDIDO : contem
    PRODUTO ||--o{ ITEM_PEDIDO : compoe
    UNIDADE ||--o{ ESTOQUE : possui
    PRODUTO ||--o{ ESTOQUE : contabilizado
    PEDIDO ||--o{ PAGAMENTO : recebe
    USUARIO ||--o{ CONSENTIMENTO_LGPD : registra
    USUARIO ||--o| PONTUACAO_FIDELIDADE : possui
    USUARIO ||--o{ MOVIMENTO_PONTOS : gera
    PEDIDO ||--o{ MOVIMENTO_PONTOS : origina
    UNIDADE ||--o{ MOVIMENTO_ESTOQUE : registra
    PRODUTO ||--o{ MOVIMENTO_ESTOQUE : movimenta
    USUARIO ||--o{ MOVIMENTO_ESTOQUE : executa
    USUARIO ||--o{ AUDITORIA : pratica
```

## Regras de integridade
- E-mail de usuário é único.
- Estoque tem combinação única de unidade e produto.
- Quantidade de item precisa ser maior que zero.
- Cada item guarda preço unitário histórico do momento do pedido.
- Chave de idempotência, quando informada, é única.
- Movimentos de estoque e pontos registram o motivo da operação.
