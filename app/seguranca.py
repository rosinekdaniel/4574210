import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .banco_de_dados import obter_sessao_banco
from .modelos import Usuario, Perfil

SECRET_KEY = os.getenv("SECRET_KEY", "chave-apenas-para-desenvolvimento")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
codificador_senhas = PasswordHash.recommended()
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def gerar_hash_senha(password: str) -> str:
    return codificador_senhas.hash(password)

def verificar_senha(password: str, hashed: str) -> bool:
    return codificador_senhas.verify(password, hashed)

def criar_token(user: Usuario) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user.id), "perfil": user.perfil.value, "exp": expiration},
        SECRET_KEY, algorithm=ALGORITHM
    )

def usuario_atual(token: str = Depends(esquema_oauth2), db: Session = Depends(obter_sessao_banco)):
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erro_credenciais
    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo:
        raise erro_credenciais
    return usuario

def exigir_perfis(*perfis: Perfil):
    def verificar_perfil(usuario: Usuario = Depends(usuario_atual)):
        if usuario.perfil not in perfis:
            raise HTTPException(status_code=403, detail="Seu perfil não tem permissão para esta operação")
        return usuario
    return verificar_perfil
