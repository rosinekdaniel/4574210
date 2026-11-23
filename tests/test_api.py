import os
import pytest
from fastapi.testclient import TestClient

# Cada execução de teste usa um banco isolado.
os.environ["DATABASE_URL"] = "sqlite:///./test_raizes.db"

from app.principal import app

client = TestClient(app)

@pytest.fixture
def cliente_token():
    response = client.post("/api/auth/login", json={
        "email": "cliente@raizes.com", "senha": "12345678"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def gerente_token():
    response = client.post("/api/auth/login", json={
        "email": "gerente@raizes.com", "senha": "12345678"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def test_01_login_valido():
    r = client.post("/api/auth/login", json={"email":"cliente@raizes.com","senha":"12345678"})
    assert r.status_code == 200 and "access_token" in r.json()

def test_02_login_senha_incorreta():
    r = client.post("/api/auth/login", json={"email":"cliente@raizes.com","senha":"senha-errada"})
    assert r.status_code == 401

def test_03_rota_protegida_sem_token():
    assert client.get("/api/produtos").status_code == 401

def test_04_cadastro_usuario_valido():
    r = client.post("/api/usuarios", json={
        "nome":"Pessoa Teste", "email":"pessoa.teste@example.com", "senha":"senha-forte-123"
    })
    assert r.status_code in (201, 409)

def test_05_cadastro_email_invalido():
    r = client.post("/api/usuarios", json={"nome":"Teste", "email":"nao-e-email", "senha":"senha-forte"})
    assert r.status_code == 422

def test_06_listar_produtos_com_token(cliente_token):
    r = client.get("/api/produtos", headers=auth(cliente_token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_07_criar_pedido_valido(cliente_token):
    r = client.post("/api/pedidos", headers={**auth(cliente_token), "Idempotency-Key":"teste-pedido-001"},
                    json={"unidade_id":1,"canal_pedido":"APP","itens":[{"produto_id":1,"quantidade":1}]})
    assert r.status_code in (201, 409)

def test_08_produto_inexistente(cliente_token):
    r = client.post("/api/pedidos", headers=auth(cliente_token),
                    json={"unidade_id":1,"canal_pedido":"APP","itens":[{"produto_id":99999,"quantidade":1}]})
    assert r.status_code == 404

def test_09_canal_pedido_invalido(cliente_token):
    r = client.post("/api/pedidos", headers=auth(cliente_token),
                    json={"unidade_id":1,"canal_pedido":"DRONE","itens":[{"produto_id":1,"quantidade":1}]})
    assert r.status_code == 422

def test_10_estoque_movimento_sem_permissao(cliente_token):
    r = client.post("/api/estoque/movimentos", headers=auth(cliente_token),
                    json={"unidade_id":1,"produto_id":1,"tipo":"ENTRADA","quantidade":1,"motivo":"Reposição"})
    assert r.status_code == 403

def test_11_consentimento_lgpd(cliente_token):
    r = client.post("/api/lgpd/consentimentos", headers=auth(cliente_token),
                    json={"finalidade":"Comunicação promocional","consentido":False,"versao_termo":"1.0"})
    assert r.status_code == 201

def test_12_listar_promocoes(cliente_token):
    r = client.get("/api/promocoes", headers=auth(cliente_token))
    assert r.status_code == 200

def test_13_fidelidade_consultar(cliente_token):
    r = client.get("/api/fidelidade", headers=auth(cliente_token))
    assert r.status_code == 200 and "pontos" in r.json()

def test_14_verificar_saude():
    assert client.get("/verificar_saude").status_code == 200
