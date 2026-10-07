# Dockerfile = a "receita" da imagem da aplicação. O "docker build"
# executa as instruções de cima para baixo.

FROM python:3.13-slim
# Ponto de partida: uma imagem oficial com Linux + Python 3.13 já
# instalados. "slim" é a versão enxuta (menor, baixa mais rápido).
ENV POETRY_VIRTUALENVS_CREATE=false
# Diz ao Poetry para NÃO criar um ambiente virtual (.venv): o container
# já é isolado por si só, então as dependências vão direto no Python da
# imagem. Por isso o entrypoint.sh chama alembic e uvicorn sem
# "poetry run".

WORKDIR app/
# Cria (se preciso) e entra na pasta /app dentro do container. Os
# próximos comandos rodam a partir dela.
COPY . .
# Copia os arquivos do projeto (o "." da sua máquina) para a pasta
# atual da imagem (o "." do container, ou seja, /app). É uma "foto" dos
# arquivos na hora do build: mudou o código, precisa rebuildar.

RUN pip install poetry
# Instala o Poetry dentro da imagem.

RUN poetry config installer.max-workers 10
# Deixa o Poetry instalar até 10 pacotes em paralelo (mais rápido).
RUN poetry install --no-interaction --no-ansi --without dev
# Instala as dependências do pyproject.toml/poetry.lock.
# --without dev: pula as de desenvolvimento (pytest, ruff...), que não
# são necessárias para RODAR a aplicação.
# --no-interaction / --no-ansi: sem perguntas e sem cores, já que
# ninguém está "olhando" o build.

EXPOSE 8000
# Documenta que a aplicação escuta na porta 8000. Não abre a porta
# sozinho: quem liga a porta ao seu PC é o "-p 8000:8000" (docker run)
# ou o "ports" do compose.yaml.
CMD poetry run uvicorn --host 0.0.0.0 fastapi_zero.app:app
# Comando padrão ao ligar o container (usado no "docker run").
# --host 0.0.0.0: aceita conexões vindas de fora do container. Com o
# padrão (127.0.0.1), a API só responderia ao próprio container.
# No compose.yaml, este CMD é trocado pelo entrypoint.sh.
