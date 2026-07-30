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

    # Réplicas del servicio de precios, separadas por coma. Varias porque el
    # backend reparte la carga entre ellas y saca de rotación las que fallan.
    ml_service_urls: str = "http://localhost:8001"
    # Si una réplica no contesta en este tiempo, se corta y se prueba la siguiente.
    ml_timeout_seconds: float = 2.0
    # Fallos consecutivos que tolera una réplica antes de sacarla de rotación.
    ml_failure_threshold: int = 3
    # Cuánto espera antes de volver a probar una réplica marcada como caída.
    ml_recovery_seconds: float = 30.0

    @property
    def ml_replicas(self) -> list[str]:
        """Lista de réplicas, ya limpia de espacios y entradas vacías."""
        return [u.strip().rstrip("/") for u in self.ml_service_urls.split(",") if u.strip()]

    # ".env" es relativo al directorio de ejecución, no a este archivo:
    # por eso el backend siempre se corre desde Backend/.
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()