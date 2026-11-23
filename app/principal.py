from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .banco_de_dados import Base, engine, obter_sessao_banco, SessaoLocal
from .modelos import *
from .esquemas import *
from .seguranca import *

app = FastAPI(
    title="Rede Raízes do Nordeste API",
    version="2.0.0",
    description="API acadêmica para pedidos, estoque, pagamento simulado e serviços de fidelização."
)

def registrar_auditoria(db: Session, usuario_id: int | None, acao: str,
                        entidade: str, entidade_id: int | None, detalhes: str = ""):
    db.add(Auditoria(usuario_id=usuario_id, acao=acao, entidade=entidade,
                     entidade_id=entidade_id, detalhes=detalhes))

@app.on_event("startup")
def preparar_banco():
    Base.metadata.create_all(bind=engine)
    with SessaoLocal() as db:
        if db.scalar(select(Usuario).limit(1)):
            return
        cliente = Usuario(nome="Cliente Demo", email="cliente@raizes.com",
                          senha_hash=gerar_hash_senha("12345678"), perfil=Perfil.CLIENTE)
        gerente = Usuario(nome="Gerente Demo", email="gerente@raizes.com",
                          senha_hash=gerar_hash_senha("12345678"), perfil=Perfil.GERENTE)
        cozinha = Usuario(nome="Cozinha Demo", email="cozinha@raizes.com",
                          senha_hash=gerar_hash_senha("12345678"), perfil=Perfil.COZINHA)
        unidade = Unidade(nome="Raízes do Nordeste - Centro", endereco="Rua Principal, 100",
                          cidade="Curitiba", estado="PR")
        produto = Produto(nome="Baião de Dois", categoria="Pratos", preco=Decimal("20.00"))
        db.add_all([cliente, gerente, cozinha, unidade, produto])
        db.flush()
        db.add(Estoque(unidade_id=unidade.id, produto_id=produto.id, quantidade=50))
        db.add(PontuacaoFidelidade(usuario_id=cliente.id, pontos=0))
        db.commit()

@app.get("/verificar_saude", tags=["Sistema"])
def verificar_saude():
    return {"status": "ok"}

@app.post("/api/usuarios", status_code=201, tags=["Usuários"])
def cadastrar_usuario(req: CadastroUsuario, db: Session = Depends(obter_sessao_banco)):
    if db.scalar(select(Usuario).where(Usuario.email == req.email)):
        raise HTTPException(409, "Já existe uma conta com este e-mail")
    usuario = Usuario(nome=req.nome.strip(), email=req.email,
                      senha_hash=gerar_hash_senha(req.senha), perfil=Perfil.CLIENTE)
    db.add(usuario)
    db.flush()
    db.add(PontuacaoFidelidade(usuario_id=usuario.id, pontos=0))
    registrar_auditoria(db, usuario.id, "CADASTRAR_USUARIO", "USUARIO", usuario.id)
    db.commit()
    return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.perfil}

@app.post("/api/auth/login", response_model=RespostaLogin, tags=["Autenticação"])
def login(req: RequisicaoLogin, db: Session = Depends(obter_sessao_banco)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == req.email))
    if not usuario or not verificar_senha(req.senha, usuario.senha_hash):
        raise HTTPException(401, "E-mail ou senha incorretos")
    return RespostaLogin(access_token=criar_token(usuario))

@app.get("/api/produtos", response_model=list[RespostaProduto], tags=["Produtos"])
def listar_produtos(db: Session = Depends(obter_sessao_banco), usuario: Usuario = Depends(usuario_atual)):
    return list(db.scalars(select(Produto).where(Produto.ativo.is_(True))))

@app.post("/api/pedidos", response_model=RespostaPedido, status_code=201, tags=["Pedidos"])
def criar_pedido(req: RequisicaoCriarPedido, db: Session = Depends(obter_sessao_banco),
                 idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                 usuario: Usuario = Depends(exigir_perfis(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN))):
    # Repetir a mesma chave devolve o pedido anterior, evitando duplicidade por reenvio.
    if idempotency_key:
        existente = db.scalar(select(Pedido).where(Pedido.chave_idempotencia == idempotency_key))
        if existente:
            if existente.usuario_id != usuario.id:
                raise HTTPException(409, "Esta chave de idempotência já foi utilizada")
            return existente

    unidade = db.get(Unidade, req.unidade_id)
    if not unidade or not unidade.ativa:
        raise HTTPException(404, "Unidade não encontrada")

    pedido = Pedido(usuario_id=usuario.id, unidade_id=unidade.id,
                    canal_pedido=req.canal_pedido, status=StatusPedido.AGUARDANDO_PAGAMENTO,
                    valor_total=Decimal("0"), chave_idempotencia=idempotency_key)
    total = Decimal("0")
    # Validamos todos os itens antes de confirmar a transação.
    itens_validados = []
    for item in req.itens:
        produto = db.get(Produto, item.produto_id)
        if not produto or not produto.ativo:
            raise HTTPException(404, f"Produto {item.produto_id} não encontrado")
        estoque = db.scalar(select(Estoque).where(
            Estoque.unidade_id == unidade.id, Estoque.produto_id == produto.id
        ))
        if not estoque or estoque.quantidade < item.quantidade:
            raise HTTPException(409, f"Estoque insuficiente para o produto {produto.id}")
        itens_validados.append((item, produto, estoque))

    for item, produto, estoque in itens_validados:
        estoque.quantidade -= item.quantidade
        subtotal = produto.preco * item.quantidade
        pedido.itens.append(ItemPedido(produto_id=produto.id, quantidade=item.quantidade,
                                       preco_unitario=produto.preco, subtotal=subtotal))
        total += subtotal

    pedido.valor_total = total
    db.add(pedido)
    db.flush()
    for item, produto, estoque in itens_validados:
        db.add(MovimentoEstoque(unidade_id=unidade.id, produto_id=produto.id,
                                usuario_id=usuario.id, tipo="SAIDA", quantidade=item.quantidade,
                                motivo=f"Reserva para pedido {pedido.id}"))
    registrar_auditoria(db, usuario.id, "CRIAR_PEDIDO", "PEDIDO", pedido.id,
                        f"Canal: {req.canal_pedido.value}; total: {total}")
    db.commit()
    db.refresh(pedido)
    return pedido

@app.get("/api/pedidos", response_model=list[RespostaPedido], tags=["Pedidos"])
def listar_pedidos(canal_pedido: CanalPedido | None = None, pagina: int = 1, tamanho: int = 20,
                   db: Session = Depends(obter_sessao_banco), usuario: Usuario = Depends(usuario_atual)):
    if pagina < 1 or tamanho < 1 or tamanho > 100:
        raise HTTPException(400, "Use pagina >= 1 e tamanho entre 1 e 100")
    consulta = select(Pedido).order_by(Pedido.id.desc())
    if canal_pedido:
        consulta = consulta.where(Pedido.canal_pedido == canal_pedido)
    return list(db.scalars(consulta.offset((pagina - 1) * tamanho).limit(tamanho)))

@app.get("/api/pedidos/{pedido_id}", response_model=RespostaPedido, tags=["Pedidos"])
def consultar_pedido(pedido_id: int, db: Session = Depends(obter_sessao_banco),
                     usuario: Usuario = Depends(usuario_atual)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    if usuario.perfil == Perfil.CLIENTE and pedido.usuario_id != usuario.id:
        raise HTTPException(403, "Você só pode consultar os próprios pedidos")
    return pedido

@app.post("/api/pedidos/{pedido_id}/pagamento", tags=["Pagamentos"])
def pagar(pedido_id: int, req: RequisicaoPagamento, db: Session = Depends(obter_sessao_banco),
          usuario: Usuario = Depends(usuario_atual)):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    if usuario.perfil == Perfil.CLIENTE and pedido.usuario_id != usuario.id:
        raise HTTPException(403, "Você só pode pagar os próprios pedidos")
    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise HTTPException(409, "O pedido não está aguardando pagamento")

    status_pagamento = StatusPagamento.APROVADO if req.aprovar else StatusPagamento.RECUSADO
    db.add(Pagamento(pedido_id=pedido.id, metodo=req.metodo, valor=pedido.valor_total,
                     status=status_pagamento, transacao_mock=f"MOCK-{uuid4().hex[:12]}"))
    if req.aprovar:
        pedido.status = StatusPedido.AGUARDANDO_PREPARACAO
        # Regra demonstrativa: 1 ponto por real completo pago.
        pontos = int(pedido.valor_total)
        carteira = db.scalar(select(PontuacaoFidelidade).where(PontuacaoFidelidade.usuario_id == pedido.usuario_id))
        if not carteira:
            carteira = PontuacaoFidelidade(usuario_id=pedido.usuario_id, pontos=0)
            db.add(carteira)
            db.flush()
        carteira.pontos += pontos
        db.add(MovimentoPontos(usuario_id=pedido.usuario_id, pedido_id=pedido.id,
                               pontos=pontos, motivo="Pontos por pedido aprovado"))
    else:
        pedido.status = StatusPedido.CANCELADO
        for item in pedido.itens:
            estoque = db.scalar(select(Estoque).where(
                Estoque.unidade_id == pedido.unidade_id, Estoque.produto_id == item.produto_id
            ))
            if estoque:
                estoque.quantidade += item.quantidade
                db.add(MovimentoEstoque(unidade_id=pedido.unidade_id, produto_id=item.produto_id,
                                        usuario_id=usuario.id, tipo="ENTRADA", quantidade=item.quantidade,
                                        motivo=f"Devolução por pagamento recusado do pedido {pedido.id}"))
    registrar_auditoria(db, usuario.id, "PAGAMENTO", "PEDIDO", pedido.id, status_pagamento.value)
    db.commit()
    return {"pedido_id": pedido.id, "status_pagamento": status_pagamento, "status_pedido": pedido.status}

@app.patch("/api/pedidos/{pedido_id}/status", response_model=RespostaPedido, tags=["Pedidos"])
def atualizar_status(pedido_id: int, req: RequisicaoAtualizarStatus, db: Session = Depends(obter_sessao_banco),
                     usuario: Usuario = Depends(exigir_perfis(Perfil.COZINHA, Perfil.GERENTE, Perfil.ADMIN))):
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    transicoes = {
        StatusPedido.AGUARDANDO_PREPARACAO: {StatusPedido.EM_PREPARACAO},
        StatusPedido.EM_PREPARACAO: {StatusPedido.PRONTO},
        StatusPedido.PRONTO: {StatusPedido.ENTREGUE},
    }
    if req.status not in transicoes.get(pedido.status, set()):
        raise HTTPException(409, "Transição de status inválida")
    pedido.status = req.status
    pedido.atualizado_em = datetime.utcnow()
    registrar_auditoria(db, usuario.id, "ALTERAR_STATUS", "PEDIDO", pedido.id, req.status.value)
    db.commit()
    db.refresh(pedido)
    return pedido

@app.post("/api/estoque/movimentos", status_code=201, tags=["Estoque"])
def movimentar_estoque(req: RequisicaoMovimentoEstoque, db: Session = Depends(obter_sessao_banco),
                       usuario: Usuario = Depends(exigir_perfis(Perfil.GERENTE, Perfil.ADMIN))):
    tipo = req.tipo.upper()
    if tipo not in {"ENTRADA", "SAIDA", "AJUSTE"}:
        raise HTTPException(422, "Tipo deve ser ENTRADA, SAIDA ou AJUSTE")
    unidade = db.get(Unidade, req.unidade_id)
    produto = db.get(Produto, req.produto_id)
    if not unidade or not produto:
        raise HTTPException(404, "Unidade ou produto não encontrado")
    estoque = db.scalar(select(Estoque).where(
        Estoque.unidade_id == unidade.id, Estoque.produto_id == produto.id
    ))
    if not estoque:
        estoque = Estoque(unidade_id=unidade.id, produto_id=produto.id, quantidade=0)
        db.add(estoque)
        db.flush()
    if tipo == "ENTRADA":
        estoque.quantidade += req.quantidade
    elif tipo == "SAIDA":
        if estoque.quantidade < req.quantidade:
            raise HTTPException(409, "Estoque insuficiente")
        estoque.quantidade -= req.quantidade
    else:
        estoque.quantidade = req.quantidade
    movimento = MovimentoEstoque(unidade_id=unidade.id, produto_id=produto.id,
                                 usuario_id=usuario.id, tipo=tipo,
                                 quantidade=req.quantidade, motivo=req.motivo)
    db.add(movimento)
    registrar_auditoria(db, usuario.id, "MOVIMENTAR_ESTOQUE", "ESTOQUE", estoque.id, tipo)
    db.commit()
    return {"mensagem": "Movimentação registrada", "quantidade_atual": estoque.quantidade}

@app.get("/api/estoque", tags=["Estoque"])
def consultar_estoque(unidade_id: int, db: Session = Depends(obter_sessao_banco),
                      usuario: Usuario = Depends(exigir_perfis(Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN, Perfil.COZINHA))):
    registros = db.scalars(select(Estoque).where(Estoque.unidade_id == unidade_id)).all()
    return [{"produto_id": r.produto_id, "quantidade": r.quantidade} for r in registros]

@app.post("/api/lgpd/consentimentos", status_code=201, tags=["LGPD"])
def registrar_consentimento(req: RequisicaoConsentimento, db: Session = Depends(obter_sessao_banco),
                            usuario: Usuario = Depends(usuario_atual)):
    consentimento = ConsentimentoLGPD(usuario_id=usuario.id, finalidade=req.finalidade,
                                      consentido=req.consentido, versao_termo=req.versao_termo)
    db.add(consentimento)
    registrar_auditoria(db, usuario.id, "REGISTRAR_CONSENTIMENTO", "CONSENTIMENTO_LGPD", None,
                        f"Finalidade={req.finalidade}; consentido={req.consentido}")
    db.commit()
    return {"mensagem": "Preferência de consentimento registrada", "consentido": req.consentido}

@app.get("/api/lgpd/consentimentos", tags=["LGPD"])
def listar_meus_consentimentos(db: Session = Depends(obter_sessao_banco),
                               usuario: Usuario = Depends(usuario_atual)):
    registros = db.scalars(select(ConsentimentoLGPD).where(
        ConsentimentoLGPD.usuario_id == usuario.id
    ).order_by(ConsentimentoLGPD.registrado_em.desc())).all()
    return [{"finalidade": r.finalidade, "consentido": r.consentido,
             "versao_termo": r.versao_termo, "registrado_em": r.registrado_em} for r in registros]

@app.get("/api/fidelidade", tags=["Fidelidade"])
def consultar_pontos(db: Session = Depends(obter_sessao_banco), usuario: Usuario = Depends(usuario_atual)):
    carteira = db.scalar(select(PontuacaoFidelidade).where(PontuacaoFidelidade.usuario_id == usuario.id))
    return {"pontos": carteira.pontos if carteira else 0}

@app.post("/api/fidelidade/resgates", tags=["Fidelidade"])
def resgatar_pontos(req: RequisicaoResgatePontos, db: Session = Depends(obter_sessao_banco),
                    usuario: Usuario = Depends(usuario_atual)):
    carteira = db.scalar(select(PontuacaoFidelidade).where(PontuacaoFidelidade.usuario_id == usuario.id))
    if not carteira or carteira.pontos < req.pontos:
        raise HTTPException(409, "Saldo de pontos insuficiente")
    carteira.pontos -= req.pontos
    db.add(MovimentoPontos(usuario_id=usuario.id, pontos=-req.pontos,
                           motivo="Resgate solicitado pelo cliente"))
    registrar_auditoria(db, usuario.id, "RESGATAR_PONTOS", "FIDELIDADE", usuario.id,
                        f"Pontos resgatados: {req.pontos}")
    db.commit()
    return {"mensagem": "Resgate registrado", "saldo_atual": carteira.pontos}

@app.post("/api/promocoes", status_code=201, tags=["Promoções"])
def criar_promocao(req: RequisicaoCriarPromocao, db: Session = Depends(obter_sessao_banco),
                   usuario: Usuario = Depends(exigir_perfis(Perfil.GERENTE, Perfil.ADMIN))):
    promocao = Promocao(nome=req.nome, descricao=req.descricao,
                        percentual_desconto=req.percentual_desconto, ativa=True)
    db.add(promocao)
    db.flush()
    registrar_auditoria(db, usuario.id, "CRIAR_PROMOCAO", "PROMOCAO", promocao.id)
    db.commit()
    return {"id": promocao.id, "nome": promocao.nome,
            "percentual_desconto": promocao.percentual_desconto, "ativa": promocao.ativa}

@app.get("/api/promocoes", tags=["Promoções"])
def listar_promocoes(db: Session = Depends(obter_sessao_banco), usuario: Usuario = Depends(usuario_atual)):
    promocoes = db.scalars(select(Promocao).where(Promocao.ativa.is_(True))).all()
    return [{"id": p.id, "nome": p.nome, "descricao": p.descricao,
             "percentual_desconto": p.percentual_desconto} for p in promocoes]
