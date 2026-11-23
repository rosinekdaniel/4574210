# Plano de testes

| ID | Cenário | Resultado esperado |
|---|---|---|
| CT01 | Login válido | 200 e token |
| CT02 | Senha incorreta | 401 |
| CT03 | Rota protegida sem token | 401 |
| CT04 | Cadastro válido | 201 |
| CT05 | E-mail inválido | 422 |
| CT06 | Listar produtos autenticado | 200 |
| CT07 | Criar pedido válido | 201 |
| CT08 | Produto inexistente | 404 |
| CT09 | Canal de pedido inválido | 422 |
| CT10 | Cliente tenta movimentar estoque | 403 |
| CT11 | Registrar consentimento LGPD | 201 |
| CT12 | Listar promoções | 200 |
| CT13 | Consultar pontos | 200 |
| CT14 | Health check | 200 |

Execute `pytest -v`. Alguns testes de criação podem ser afetados por estado persistido no banco de teste; para repetição confiável, use banco temporário limpo por sessão e valide cada resposta ao executar localmente.
