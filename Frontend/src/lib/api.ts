/**
 * Cliente de la API. Único punto donde el frontend habla con el Backend.
 *
 * Centralizarlo evita repetir en cada componente la URL base, las cabeceras, el
 * token y el manejo de errores. Ningún componente debe llamar a fetch() directo.
 */

import type {
  Booking,
  BookingCreate,
  PriceSuggestion,
  PriceSuggestionRequest,
  Property,
  PropertyCreate,
  PropertyUpdate,
  Token,
  User,
  UserCreate,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "stay_direct_token";

/** Error de la API con el código HTTP, para que quien llame pueda distinguir
 *  un 401 (no autenticado) de un 409 (fechas ocupadas) o un 503 (ML caído). */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// El token se guarda en localStorage, que solo existe en el navegador: en el
// servidor (Server Components) estas funciones devuelven null sin romper.
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

/**
 * Envoltura de fetch: arma la URL, adjunta el token si existe y traduce los
 * errores HTTP a ApiError con el mensaje que devolvió el Backend.
 */
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    // FastAPI manda el motivo en "detail". Puede ser texto o una lista de
    // errores de validación (422), así que se normaliza a un solo mensaje.
    let message = `Error ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((e: { msg: string }) => e.msg).join(", ");
      }
    } catch {
      // Respuesta sin cuerpo JSON: se queda el mensaje genérico.
    }
    throw new ApiError(response.status, message);
  }

  // 204 No Content no trae cuerpo que parsear.
  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

export const api = {
  // ---------- Autenticación ----------

  register(data: UserCreate): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /** El login usa form-urlencoded, no JSON: es lo que espera el estándar
   *  OAuth2 de FastAPI, y el campo se llama "username" aunque sea el email. */
  async login(email: string, password: string): Promise<Token> {
    const body = new URLSearchParams({ username: email, password });

    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });

    if (!response.ok) {
      throw new ApiError(response.status, "Correo o contraseña incorrectos");
    }

    const token: Token = await response.json();
    setToken(token.access_token);
    return token;
  },

  logout(): void {
    clearToken();
  },

  me(): Promise<User> {
    return request<User>("/auth/me");
  },

  // ---------- Propiedades ----------

  listProperties(): Promise<Property[]> {
    return request<Property[]>("/properties");
  },

  getProperty(id: number): Promise<Property> {
    return request<Property>(`/properties/${id}`);
  },

  createProperty(data: PropertyCreate): Promise<Property> {
    return request<Property>("/properties", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateProperty(id: number, data: PropertyUpdate): Promise<Property> {
    return request<Property>(`/properties/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteProperty(id: number): Promise<void> {
    return request<void>(`/properties/${id}`, { method: "DELETE" });
  },

  // ---------- Reservas ----------

  createBooking(data: BookingCreate): Promise<Booking> {
    return request<Booking>("/bookings", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /** Solo las reservas del usuario del token: el Backend filtra por guest_id,
   *  el frontend no puede pedir las de alguien más. */
  listMyBookings(): Promise<Booking[]> {
    return request<Booking[]>("/bookings");
  },

  cancelBooking(id: number): Promise<Booking> {
    return request<Booking>(`/bookings/${id}/cancel`, { method: "POST" });
  },

  // ---------- Sugerencia de precio ----------

  suggestPrice(data: PriceSuggestionRequest): Promise<PriceSuggestion> {
    return request<PriceSuggestion>("/pricing/suggest", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};
