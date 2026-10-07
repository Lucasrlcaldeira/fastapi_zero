#!/bin/sh
# "Shebang": diz ao Linux do container qual programa executa este
# script (o shell "sh"). Precisa ser a PRIMEIRA linha do arquivo.

# Script que o compose.yaml roda ao ligar o container da API.

# Executa as migrações do banco de dados
alembic upgrade head
# Cria/atualiza as tabelas no Postgres do compose. Assim o banco já
# fica com a estrutura certa antes de a API começar a atender.

# Inicia a aplicação
uvicorn --host 0.0.0.0 --port 8000 fastapi_zero.app:app
# Sobe o servidor. --host 0.0.0.0 aceita conexões de fora do container
# (veja o Dockerfile).
#
# ⚠️ Salve este arquivo com quebra de linha LF (padrão do Linux), não
# CRLF (padrão do Windows). Com CRLF, o container não acha o "sh\r" e
# falha com "no such file or directory".