from datetime import datetime

# Tipo usado para representar data e hora do campo created_at.
from sqlalchemy import func

# func dá acesso a funções do próprio banco de dados, como NOW()
# (data/hora atual), usada abaixo para o valor padrão de created_at.
from sqlalchemy.orm import Mapped, mapped_column, registry

# Mapped: anotação de tipo que diz ao SQLAlchemy qual é o tipo da coluna.
# mapped_column: configura detalhes de cada coluna (chave primária,
# valor padrão, se é única etc.).
# registry: "catálogo" que guarda o mapeamento entre classes Python e
# tabelas do banco.

table_registry = registry()
# Cria o registro que será usado para mapear todos os models do
# projeto (aqui, só o User). É reaproveitado em migrations/env.py e
# nos testes para criar/derrubar as tabelas.


@table_registry.mapped_as_dataclass()
# Decorador que faz duas coisas: registra a classe como uma tabela do
# banco E transforma a classe num dataclass Python (ganha __init__,
# __repr__, comparação de igualdade etc. automaticamente).
class User:
    __tablename__ = 'users'
    # Nome da tabela no banco de dados.

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    # Chave primária, gerada automaticamente pelo banco.
    # init=False remove esse campo do __init__ do dataclass, já que
    # quem cria o id é o próprio banco, não quem instancia a classe.

    username: Mapped[str] = mapped_column(unique=True)
    # Nome de usuário; unique=True impede dois usuários com o mesmo
    # username.

    email: Mapped[str] = mapped_column(unique=True)
    # E-mail; também precisa ser único.

    password: Mapped[str]
    # Senha armazenada como texto simples (ainda sem hash/criptografia
    # nesta fase do curso).

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    # Data/hora de criação do registro. init=False porque não é
    # informado manualmente; server_default=func.now() faz o próprio
    # banco preencher com o momento exato da inserção.

    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
