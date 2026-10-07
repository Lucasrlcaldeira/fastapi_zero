from http import HTTPStatus
from typing import Annotated

# Query: avisa o FastAPI que um parâmetro vem da URL, depois do "?"
# (ex: /todos/?title=mercado&limit=5).
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import Todo, User

# Os schemas das tarefas (veja schemas.py): o que entra e o que sai de
# cada rota deste arquivo.
from fastapi_zero.schemas import (
    FilterTodo,
    Message,
    TodoList,
    TodoPublic,
    TodoSchema,
    TodoUpdate,
)
from fastapi_zero.security import get_current_user

router = APIRouter(prefix='/todos', tags=['todos'])
# Todas as rotas deste arquivo começam com /todos e aparecem agrupadas
# como "todos" no /docs.

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
# Os mesmos atalhos de users.py. Como TODAS as rotas daqui pedem
# CurrentUser, nenhuma funciona sem token: cada pessoa só mexe nas
# próprias tarefas.


@router.post('/', response_model=TodoPublic)
async def create_todo(
    todo: TodoSchema,
    session: Session,
    user: CurrentUser,
):
    # Cria uma tarefa. O "todo" é o JSON enviado pelo cliente (title,
    # description e state), já validado pelo TodoSchema.
    db_todo = Todo(
        title=todo.title,
        description=todo.description,
        state=todo.state,
        user_id=user.id,
    )
    # Transforma o schema (Pydantic) num model (SQLAlchemy), que é o que
    # o banco entende. Repare no user_id: o DONO da tarefa vem do token,
    # não do JSON. Assim ninguém consegue criar tarefa em nome de outro.

    session.add(db_todo)
    await session.commit()
    await session.refresh(db_todo)
    # add coloca na fila, commit grava no banco e refresh relê o registro
    # para preencher o id, que quem gera é o banco.

    return db_todo
    # O response_model=TodoPublic transforma o objeto em JSON com
    # id, title, description e state.


@router.get('/', response_model=TodoList)
async def list_todos(
    user: CurrentUser,
    session: Session,
    todo_filter: Annotated[FilterTodo, Query()],
):
    # Lista as tarefas do usuário logado, com filtros OPCIONAIS.
    # Query() faz o FastAPI montar o FilterTodo a partir da URL.
    # Ex: GET /todos/?title=mercado vira
    # FilterTodo(offset=0, limit=10, title='mercado',
    #            description=None, state=None).
    # O que não vier na URL fica com o valor padrão (None, 0 ou 10).

    query = select(Todo).where(Todo.user_id == user.id)
    # Aqui a consulta é só MONTADA, ainda não foi ao banco. É um
    # "rascunho" de SQL que vamos completando nos ifs abaixo:
    #   SELECT * FROM todos WHERE user_id = <id do usuário logado>

    if todo_filter.title:
        query = query.filter(Todo.title.contains(todo_filter.title))
    # Só filtra se o usuário mandou ?title=... (se veio None, pula).
    # Atenção aos dois "title":
    # - Todo.title é a COLUNA do banco;
    # - todo_filter.title é o TEXTO que veio na URL.
    # .contains() vira um LIKE no SQL, ou seja, "contém em qualquer
    # posição": title LIKE '%mercado%' acha "Ir ao mercado".
    # .filter() não altera a query antiga: devolve uma NOVA query com a
    # condição a mais. Por isso o resultado é guardado de volta em
    # "query"; sem o "query =", o filtro se perderia.

    if todo_filter.description:
        query = query.filter(
            Todo.description.contains(todo_filter.description)
        )
    # Mesma ideia, agora na descrição: ?description=desc acha
    # "description", porque "desc" está contido no texto.

    if todo_filter.state:
        query = query.filter(Todo.state == todo_filter.state)
    # Para o estado, a comparação é EXATA (==), e não "contém": a tarefa
    # é "draft" ou não é. Além disso, no PostgreSQL a coluna state é do
    # tipo Enum, e o LIKE do .contains() só funciona com texto (dá o
    # erro "operator does not exist: todostate ~~ text").
    # Os filtros vão se EMPILHANDO: com ?title=a&state=done, o SQL fica
    # WHERE user_id = 1 AND title LIKE '%a%' AND state = 'done'.

    todos = await session.scalars(
        query.limit(todo_filter.limit).offset(todo_filter.offset)
    )
    # Só AGORA a consulta vai ao banco (por isso o await).
    # Paginação: offset = quantas tarefas pular; limit = quantas trazer.
    # Ex: ?offset=1&limit=2 pula a 1ª tarefa e devolve a 2ª e a 3ª.
    # scalars() devolve os objetos Todo (e não linhas "cruas").

    return {'todos': todos.all()}
    # .all() transforma o resultado numa lista. A chave "todos" é a
    # exigida pelo schema TodoList.


@router.delete('/{todo_id}', response_model=Message)
async def delete_todo(todo_id: int, session: Session, user: CurrentUser):
    # Apaga uma tarefa. O todo_id vem do caminho da URL
    # (ex: DELETE /todos/3 → todo_id=3).
    todo = await session.scalar(
        select(Todo).where(Todo.user_id == user.id, Todo.id == todo_id)
    )
    # Busca a tarefa por DUAS condições ao mesmo tempo (a vírgula no
    # where funciona como AND): o id certo E pertencer ao usuário
    # logado. Se a tarefa for de outra pessoa, a busca volta vazia.

    if not todo:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Task not found.'
        )
    # 404 tanto para "não existe" quanto para "é de outra pessoa".
    # Responder 403 entregaria que aquela tarefa existe; com 404, quem
    # não é dono não descobre nada.

    await session.delete(todo)
    await session.commit()

    return {'message': 'Task has been deleted successfully.'}


@router.patch('/{todo_id}', response_model=TodoPublic)
async def patch_todo(
    todo_id: int, session: Session, user: CurrentUser, todo: TodoUpdate
):
    # Altera PARTE de uma tarefa. Diferença entre PUT e PATCH:
    # - PUT (usado em users.py) troca o registro INTEIRO, então todos os
    #   campos precisam ser enviados;
    # - PATCH muda só os campos enviados. Ex: {"state": "done"} marca a
    #   tarefa como feita sem mexer no título nem na descrição.
    db_todo = await session.scalar(
        select(Todo).where(Todo.user_id == user.id, Todo.id == todo_id)
    )
    # Mesma busca segura do delete: id certo E dono certo.

    if not db_todo:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Task not found.'
        )

    for key, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, value)
    # O coração do PATCH:
    # - model_dump() transforma o schema num dicionário;
    # - exclude_unset=True deixa de fora os campos que o cliente NÃO
    #   enviou. Mandando {"title": "novo"}, o dicionário fica só
    #   {'title': 'novo'} (sem description=None e state=None);
    # - setattr(objeto, 'title', 'novo') é o mesmo que
    #   db_todo.title = 'novo', mas com o nome do campo numa variável.
    #   Assim o loop serve para qualquer campo.

    session.add(db_todo)
    await session.commit()
    await session.refresh(db_todo)

    return db_todo
