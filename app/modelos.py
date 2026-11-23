from datetime import datetime
from decimal import Decimal
from enum import Enum as EnumPython
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Numeric, ForeignKey, Enum,
    UniqueConstraint, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .banco_de_dados import Base

class Perfil(str, EnumPython):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"

class CanalPedido(str, EnumPython):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"

class StatusPedido(str, EnumPython):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    AGUARDANDO_PREPARACAO = "AGUARDANDO_PREPARACAO"
    EM_PREPARACAO = "EM_PREPARACAO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

class StatusPagamento(str, EnumPython):
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"

class Usuario(Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil), default=Perfil.CLIENTE)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Unidade(Base):
    __tablename__ = "unidade"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    endereco: Mapped[str] = mapped_column(String(255))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

class Produto(Base):
    __tablename__ = "produto"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    categoria: Mapped[str] = mapped_column(String(80))
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

class Estoque(Base):
    __tablename__ = "estoque"
    __table_args__ = (UniqueConstraint("unidade_id", "produto_id", name="uq_estoque_unidade_produto"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    quantidade: Mapped[int] = mapped_column(Integer, default=0)

class MovimentoEstoque(Base):
    __tablename__ = "movimento_estoque"
    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    tipo: Mapped[str] = mapped_column(String(20))  # ENTRADA, SAIDA ou AJUSTE
    quantidade: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Pedido(Base):
    __tablename__ = "pedido"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidade.id"))
    canal_pedido: Mapped[CanalPedido] = mapped_column(Enum(CanalPedido))
    status: Mapped[StatusPedido] = mapped_column(Enum(StatusPedido))
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    chave_idempotencia: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

class ItemPedido(Base):
    __tablename__ = "item_pedido"
    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    quantidade: Mapped[int] = mapped_column(Integer)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    pedido = relationship("Pedido", back_populates="itens")

class Pagamento(Base):
    __tablename__ = "pagamento"
    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id"))
    metodo: Mapped[str] = mapped_column(String(30))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[StatusPagamento] = mapped_column(Enum(StatusPagamento))
    transacao_mock: Mapped[str] = mapped_column(String(100))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ConsentimentoLGPD(Base):
    __tablename__ = "consentimento_lgpd"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    finalidade: Mapped[str] = mapped_column(String(120))
    consentido: Mapped[bool] = mapped_column(Boolean)
    versao_termo: Mapped[str] = mapped_column(String(30))
    registrado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PontuacaoFidelidade(Base):
    __tablename__ = "pontuacao_fidelidade"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    pontos: Mapped[int] = mapped_column(Integer, default=0)

class MovimentoPontos(Base):
    __tablename__ = "movimento_pontos"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedido.id"), nullable=True)
    pontos: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(160))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Promocao(Base):
    __tablename__ = "promocao"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text)
    percentual_desconto: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

class Auditoria(Base):
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    acao: Mapped[str] = mapped_column(String(100))
    entidade: Mapped[str] = mapped_column(String(80))
    entidade_id: Mapped[int | None] = mapped_column(nullable=True)
    detalhes: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
