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

    SECRET_KEY: str
    # Chave secreta usada para ASSINAR os tokens. Quem conhece essa chave
    # consegue criar tokens válidos, então em um projeto real ela deve ficar
    # no ".env", nunca escrita direto no código.
    ALGORITHM: str
    # Algoritmo de assinatura do JWT (HMAC com SHA-256).
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # Tempo de vida do token: depois de 30 minutos é preciso logar de novo.
