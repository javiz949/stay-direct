"""Cliente del servicio de precios: balanceo de carga y tolerancia a fallos.

No es un simple `httpx.post` al microservicio. Implementa el algoritmo de
coordinación que reparte el trabajo entre las réplicas y sobrevive a sus fallos:

1. **Round-robin**: cada petición va a la siguiente réplica de la lista, para que
   el cálculo se distribuya en vez de saturar a una sola.
2. **Timeout**: si una réplica no contesta a tiempo, se corta y se prueba la
   siguiente, en lugar de dejar colgada la petición del usuario.
3. **Marcado de réplicas caídas**: tras N fallos consecutivos, la réplica sale de
   rotación por un tiempo. Así no se gasta el timeout completo en cada petición
   contra un servicio que ya se sabe caído.
4. **Recuperación automática**: pasado el enfriamiento, la réplica vuelve a
   probarse; si responde, se reintegra a la rotación.

Si TODAS las réplicas fallan se lanza `MLServiceUnavailable`, y es el service
quien decide qué hacer (usar la estimación de respaldo).
"""

import threading
import time

import httpx

from app.core.config import settings


class MLServiceUnavailable(Exception):
    """Ninguna réplica pudo atender la petición."""


class _ReplicaState:
    """Salud de una réplica: fallos seguidos y hasta cuándo está fuera de rotación."""

    def __init__(self) -> None:
        self.consecutive_failures = 0
        self.unavailable_until = 0.0
        # Cuántas peticiones ha atendido: hace visible el reparto de carga.
        self.requests_served = 0

    def is_available(self) -> bool:
        return time.monotonic() >= self.unavailable_until

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.unavailable_until = 0.0

    def record_failure(self, threshold: int, recovery_seconds: float) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= threshold:
            self.unavailable_until = time.monotonic() + recovery_seconds


class MLClient:
    """Reparte peticiones entre las réplicas del servicio de precios."""

    def __init__(
        self,
        replicas: list[str] | None = None,
        timeout: float | None = None,
        failure_threshold: int | None = None,
        recovery_seconds: float | None = None,
    ) -> None:
        self.replicas = replicas if replicas is not None else settings.ml_replicas
        self.timeout = timeout if timeout is not None else settings.ml_timeout_seconds
        self.failure_threshold = failure_threshold or settings.ml_failure_threshold
        self.recovery_seconds = recovery_seconds or settings.ml_recovery_seconds

        self._state = {url: _ReplicaState() for url in self.replicas}
        self._next = 0
        # Uvicorn atiende los endpoints sync en un pool de hilos: sin lock, dos
        # peticiones simultáneas podrían leer y escribir el turno a la vez.
        self._lock = threading.Lock()

    def _rotation(self) -> list[str]:
        """Réplicas a intentar, empezando por la del turno. Las caídas van al final
        como último recurso: es mejor intentar con una dudosa que no responder."""
        with self._lock:
            start = self._next
            self._next = (self._next + 1) % max(len(self.replicas), 1)

        ordered = [self.replicas[(start + i) % len(self.replicas)] for i in range(len(self.replicas))]
        available = [u for u in ordered if self._state[u].is_available()]
        down = [u for u in ordered if not self._state[u].is_available()]
        return available + down

    def predict_price(self, payload: dict) -> dict:
        """Pide un precio sugerido. Prueba réplica por réplica hasta que una responda.

        Devuelve la respuesta del servicio más `served_by`, la réplica que atendió.
        Lanza MLServiceUnavailable si ninguna atiende.
        """
        if not self.replicas:
            raise MLServiceUnavailable("No hay réplicas configuradas")

        errors: list[str] = []
        for url in self._rotation():
            state = self._state[url]
            try:
                response = httpx.post(f"{url}/predict", json=payload, timeout=self.timeout)
            except httpx.RequestError as exc:
                # No hubo respuesta (caído, DNS, red, timeout): cuenta como fallo.
                state.record_failure(self.failure_threshold, self.recovery_seconds)
                errors.append(f"{url}: {type(exc).__name__}")
                continue

            if response.status_code == 200:
                state.record_success()
                state.requests_served += 1
                return {**response.json(), "served_by": url}

            # 4xx es culpa de los datos que enviamos: reintentar en otra réplica
            # daría el mismo error, así que no la penalizamos ni seguimos.
            if 400 <= response.status_code < 500:
                state.record_success()
                raise MLServiceUnavailable(f"Petición rechazada ({response.status_code})")

            # 5xx sí es problema de la réplica.
            state.record_failure(self.failure_threshold, self.recovery_seconds)
            errors.append(f"{url}: HTTP {response.status_code}")

        raise MLServiceUnavailable("Ninguna réplica respondió: " + ", ".join(errors))

    def health(self) -> list[dict]:
        """Estado de cada réplica. Sirve para diagnóstico y para la demo."""
        report = []
        for url in self.replicas:
            state = self._state[url]
            entry = {
                "url": url,
                "in_rotation": state.is_available(),
                "consecutive_failures": state.consecutive_failures,
                "requests_served": state.requests_served,
            }
            try:
                response = httpx.get(f"{url}/health", timeout=self.timeout)
                entry["reachable"] = response.status_code == 200
                if entry["reachable"]:
                    entry["model"] = response.json()
            except httpx.RequestError:
                entry["reachable"] = False
            report.append(entry)
        return report


# Una sola instancia para toda la app: el estado de salud y el turno del
# round-robin deben compartirse entre peticiones, no reiniciarse en cada una.
ml_client = MLClient()
