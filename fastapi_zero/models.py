# Tipo usado para representar data e hora dos campos created_at e
# updated_at.
from datetime import datetime
from enum import Enum

# func dá acesso a funções do próprio banco de dados, como NOW()
# (data/hora atual), usada abaixo para o valor padrão das datas.
# ForeignKey: liga uma coluna à chave primária de outra tabela.
from sqlalchemy import ForeignKey, func

# Mapped: anotação de tipo que diz ao SQLAlchemy qual é o tipo da coluna.
# mapped_column: configura detalhes de cada coluna (chave primária,
# valor padrão, se é única etc.).
# registry: "catálogo" que guarda o mapeamento entre classes Python e
# tabelas do banco.
# relationship: cria o "atalho" entre models relacionados (user.todos).
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()
# Cria o registro que será usado para mapear todos os models do
# projeto (User e Todo). É reaproveitado em migrations/env.py e
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
    # Senha do usuário. O que fica salvo aqui é o HASH da senha (gerado
    # por get_password_hash em security.py), nunca o texto digitado.

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    # Data/hora de criação do registro. init=False porque não é
    # informado manualmente; server_default=func.now() faz o próprio
    # banco preencher com o momento exato da inserção.

    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    # Data/hora da última alteração. server_default preenche na criação
    # e onupdate=func.now() atualiza sozinho a cada UPDATE feito pelo
    # SQLAlchemy. Essa coluna foi adicionada depois, pela migração
    # eebc2e224646 (veja migrations/versions/).

    todos: Mapped[list['Todo']] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    # Lista das tarefas do usuário (user.todos). Não é coluna: o
    # SQLAlchemy busca na tabela "todos" pelo user_id.
    # cascade='all, delete-orphan': apagar o usuário apaga as tarefas dele.
    # lazy='selectin': já carrega as tarefas junto, o que evita
    # consultas "escondidas" que não funcionam no modo assíncrono.


class TodoState(str, Enum):
    # Estados possíveis de uma tarefa. Herdar de str faz cada valor
    # virar texto simples no JSON e no banco ('todo', 'done'...).
    draft = 'draft'
    todo = 'todo'
    doing = 'doing'
    done = 'done'
    trash = 'trash'


@table_registry.mapped_as_dataclass()
class Todo:
    # Uma tarefa da lista de afazeres. Cada tarefa pertence a UM
    # usuário, e um usuário pode ter VÁRIAS tarefas (relação 1 para N).
    __tablename__ = 'todos'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    title: Mapped[str]
    # Título da tarefa (ex: "Ir ao mercado").
    description: Mapped[str]
    state: Mapped[TodoState]
    # Só aceita um dos valores do TodoState. No banco, vira uma coluna
    # do tipo Enum (veja a migração 99d8f5d0f16c).

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    # Quando a tarefa foi criada. Igual ao do User: init=False porque
    # ninguém informa na mão, e o banco preenche com a hora da inserção.
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    # Quando a tarefa foi alterada pela última vez (ex: num PATCH).
    # onupdate=func.now() atualiza sozinho a cada UPDATE.
    # As duas colunas vieram da migração a99cdc5af920.

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    # Chave estrangeira: guarda o id do DONO da tarefa e só aceita ids
    # que existem na tabela users. É ela que liga as duas tabelas e
    # permite o user.todos lá em cima.
