# Rede Raízes do Nordeste — Backend em Python e português

Esta versão usa português nos nomes dos módulos, modelos, funções e esquemas criados para o projeto. Os nomes das bibliotecas externas (FastAPI, SQLAlchemy e PyJWT), as rotas HTTP e os campos públicos da API são mantidos quando necessários para preservar a compatibilidade.

## Tecnologias
- Python 3.10+
- FastAPI para API REST e documentação OpenAPI
- SQLAlchemy para acesso ao banco de dados
- SQLite local ou PostgreSQL via Docker
- JWT e Argon2 para autenticação e proteção de senhas
- Pytest para testes automatizados

## Instalação e execução
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.principal:app --reload
```
Abra http://127.0.0.1:8000/docs para testar a API.

## Contas de demonstração
- Cliente: cliente@raizes.com / 12345678
- Gerente: gerente@raizes.com / 12345678
- Cozinha: cozinha@raizes.com / 12345678

Use essas contas somente no ambiente local de demonstração.

## Organização dos arquivos
- `app/principal.py`: rotas e regras principais.
- `app/modelos.py`: entidades do banco.
- `app/esquemas.py`: validação dos dados de entrada e saída.
- `app/seguranca.py`: autenticação, senhas e permissões.
- `app/banco_de_dados.py`: conexão e sessões do banco.
- `tests/test_api.py`: testes automatizados.
- `postman/`: coleção para testar as rotas.
- `docs/`: arquitetura, DER e plano de testes.

## Rotas principais
- `POST /api/usuarios` — cadastro.
- `POST /api/auth/login` — autenticação.
- `GET /api/produtos` — consulta de produtos.
- `POST /api/pedidos` — criação de pedido; aceita `Idempotency-Key`.
- `GET /api/pedidos?canal_pedido=TOTEM&pagina=1&tamanho=20` — filtro e paginação.
- `GET /api/pedidos/{id}` — consulta de pedido.
- `POST /api/pedidos/{id}/pagamento` — pagamento simulado.
- `PATCH /api/pedidos/{id}/status` — atualização de status.
- `POST /api/estoque/movimentos` — entrada, saída ou ajuste de estoque.
- `GET /api/estoque?unidade_id=1` — consulta de estoque.
- `POST` e `GET /api/lgpd/consentimentos` — consentimento.
- `GET /api/fidelidade` e `POST /api/fidelidade/resgates` — pontos.
- `POST` e `GET /api/promocoes` — promoções.

## Testes
```bash
pytest -v
```
Execute os testes localmente antes da entrega; este pacote não deve ser considerado validado até que terminem sem falhas.

## Compatibilidade
Identificadores internos podem ser traduzidos. Rotas, campos JSON, cabeçalhos HTTP e interfaces de bibliotecas externas precisam manter nomes consistentes para não quebrar a integração com Postman e outros clientes.
