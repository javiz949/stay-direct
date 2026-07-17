from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Los campos sin default (database_url, jwt_secret) truenan al arrancar si
    # faltan: preferible a fallar raro después. Los sensibles nunca llevan default.
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    admin_email: str
    admin_password: str

    # ".env" es relativo al directorio de ejecución, no a este archivo:
    # por eso el backend siempre se corre desde Backend/.
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()