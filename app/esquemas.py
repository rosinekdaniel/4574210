from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .modelos import CanalPedido, StatusPedido

class CadastroUsuario(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

class RequisicaoLogin(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)

class RespostaLogin(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RequisicaoItemPedido(BaseModel):
    produto_id: int = Field(gt=0)
    quantidade: int = Field(gt=0, le=100)

class RequisicaoCriarPedido(BaseModel):
    unidade_id: int = Field(gt=0)
    canal_pedido: CanalPedido
    itens: list[RequisicaoItemPedido] = Field(min_length=1, max_length=30)

class RequisicaoPagamento(BaseModel):
    metodo: str = Field(min_length=2, max_length=30)
    aprovar: bool = True

class RequisicaoAtualizarStatus(BaseModel):
    status: StatusPedido

class RespostaProduto(BaseModel):
    id: int
    nome: str
    categoria: str
    preco: Decimal
    model_config = ConfigDict(from_attributes=True)

class RespostaItemPedido(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    model_config = ConfigDict(from_attributes=True)

class RespostaPedido(BaseModel):
    id: int
    status: StatusPedido
    valor_total: Decimal
    canal_pedido: CanalPedido
    itens: list[RespostaItemPedido] = []
    model_config = ConfigDict(from_attributes=True)

class RequisicaoConsentimento(BaseModel):
    finalidade: str = Field(min_length=3, max_length=120)
    consentido: bool
    versao_termo: str = Field(min_length=1, max_length=30)

class RequisicaoMovimentoEstoque(BaseModel):
    unidade_id: int = Field(gt=0)
    produto_id: int = Field(gt=0)
    tipo: str
    quantidade: int = Field(gt=0)
    motivo: str = Field(min_length=3, max_length=200)

class RequisicaoResgatePontos(BaseModel):
    pontos: int = Field(gt=0)

class RequisicaoCriarPromocao(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=3, max_length=1000)
    percentual_desconto: Decimal = Field(gt=0, le=100)
