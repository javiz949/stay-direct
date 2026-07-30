"use client";

/**
 * Estado de autenticación compartido por toda la app.
 *
 * Vive en un Context porque varias partes de la interfaz necesitan saber quién
 * está dentro (el menú, las pantallas de admin, el formulario de reserva) y sin
 * esto habría que pasar el usuario por props por todo el árbol de componentes.
 *
 * Es un Client Component: el token está en localStorage, que solo existe en el
 * navegador.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, ApiError, clearToken, getToken } from "@/lib/api";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  /** true mientras se verifica el token guardado al cargar la página. Evita que
   *  la interfaz parpadee mostrando "iniciar sesión" a alguien que sí está dentro. */
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Al cargar, si hay token guardado se pregunta al Backend quién es. El token
  // puede haber expirado, así que no se confía en su sola presencia.
  useEffect(() => {
    let cancelled = false;

    async function loadUser(): Promise<User | null> {
      if (!getToken()) return null;
      try {
        return await api.me();
      } catch {
        // Token inválido o expirado: se descarta para no reintentar en cada carga.
        clearToken();
        return null;
      }
    }

    // El setState va dentro del .then y no en el cuerpo del efecto: llamarlo de
    // forma síncrona ahí dispara renders en cascada. El flag cancelled evita
    // actualizar estado si el componente ya se desmontó.
    loadUser().then((loadedUser) => {
      if (cancelled) return;
      setUser(loadedUser);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await api.login(email, password); // guarda el token
    setUser(await api.me());
  }, []);

  const logout = useCallback(() => {
    api.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, isAdmin: user?.role === "admin" }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/** Acceso al estado de autenticación. Truena si se usa fuera del provider, que
 *  es justo lo que queremos: avisa del error de programación de inmediato. */
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}

/** Traduce un error de la API al mensaje que ve el usuario (en español). */
export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  return "No se pudo conectar con el servidor";
}
