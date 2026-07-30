/**
 * Contratos de la API, espejo de los schemas de Pydantic del Backend.
 *
 * Se definen a mano en lugar de generarlos desde el OpenAPI: son pocos, la API
 * ya es estable, y así quedan legibles. Si el Backend cambia un campo, aquí
 * truena al compilar en vez de fallar en silencio en el navegador.
 */

// Enums del Backend: viajan como texto, con lista cerrada de valores.
export type Role = "guest" | "admin";
export type BookingStatus = "pending" | "confirmed" | "cancelled";

export interface Amenity {
  id: number;
  name: string;
}

/**
 * Campos que el cliente sí envía al crear una propiedad.
 *
 * Ojo con `price_per_night`: es string, no number. Pydantic serializa Decimal
 * como texto para no perder precisión en decimales, así que para hacer cuentas
 * o formatear hay que convertirlo con Number().
 */
export interface PropertyCreate {
  title: string;
  description: string;
  city: string;
  neighborhood: string;
  address: string;
  property_type: string;
  max_guests: number;
  bedrooms: number;
  bathrooms: number;
  price_per_night: string;
  is_active?: boolean;
}

// Lo que devuelve la API: los campos de creación más los que pone el servidor.
export interface Property extends PropertyCreate {
  id: number;
  created_at: string; // ISO 8601, ej. "2026-07-16T21:04:18.344403Z"
  amenities: Amenity[];
  is_active: boolean;
}

// Edición parcial: solo se envían los campos que cambian.
export type PropertyUpdate = Partial<PropertyCreate>;

// El huésped solo manda propiedad y fechas; el resto lo calcula el servidor.
export interface BookingCreate {
  property_id: number;
  check_in: string; // "YYYY-MM-DD"
  check_out: string;
}

export interface Booking {
  id: number;
  property_id: number;
  guest_id: number;
  check_in: string;
  check_out: string;
  total_price: string; // Decimal serializado como texto, igual que price_per_night
  status: BookingStatus;
  created_at: string;
}

// Rango de fechas ocupado. No trae datos del huésped a propósito: es información
// pública y no debe revelar quién se hospeda dónde.
export interface UnavailableRange {
  check_in: string; // "YYYY-MM-DD"
  check_out: string;
}

export interface PropertyAvailability {
  property_id: number;
  since: string;
  unavailable: UnavailableRange[];
}

export interface UserCreate {
  email: string;
  password: string;
}

// Sin password: la contraseña nunca viaja de vuelta.
export interface User {
  id: number;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// Sugerencia de precio: lo consulta el admin al publicar una propiedad.
export interface PriceSuggestionRequest {
  accommodates: number;
  bedrooms: number;
  bathrooms: number;
  beds: number;
  latitude: number;
  longitude: number;
  room_type: string;
  neighborhood: string;
  amenities: string[];
  minimum_nights?: number;
  maximum_nights?: number;
  bathroom_type?: string;
}

export interface PriceSuggestion {
  suggested_price: number;
  range_low: number;
  range_high: number;
  // Réplica del servicio de precios que atendió: útil para ver el balanceo.
  served_by: string | null;
}
