from pydantic_settings import BaseSettings, SettingsConfigDict

# BaseSettings: classe base que lê variáveis de ambiente e as valida
# como se fossem um schema Pydantic comum.
# SettingsConfigDict: usado para configurar de onde essas variáveis
# devem ser lidas.


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )
    # Diz ao Pydantic para carregar as variáveis a partir do arquivo
    # ".env" (na raiz do projeto), usando codificação UTF-8.

    DATABASE_URL: str
    # Declara que deve existir uma variável DATABASE_URL (texto) no
    # ".env". Se ela não existir, a aplicação falha ao iniciar — isso
    # é proposital, para evitar rodar sem saber a qual banco conectar.
