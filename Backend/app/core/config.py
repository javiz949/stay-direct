from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Sin valor default a propósito: si falta DATABASE_URL, la app truena
    # al arrancar con un error claro en vez de fallar raro más adelante.
    database_url: str

    # Ojo: ".env" es relativo al directorio desde donde se corre la app,
    # no a este archivo. Por eso el backend siempre se corre desde Backend/.
    model_config = SettingsConfigDict(env_file=".env")


# Único punto del backend que lee el .env. Los demás módulos importan este objeto.
settings = Settings()