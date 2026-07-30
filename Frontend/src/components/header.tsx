"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";

/** Barra superior: navegación y estado de la sesión. */
export function Header() {
  const { user, loading, logout, isAdmin } = useAuth();

  return (
    <header className="border-b border-neutral-200 dark:border-neutral-800">
      <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-semibold tracking-tight">
          Stay Direct
        </Link>

        <div className="flex items-center gap-4 text-sm">
          {/* Mientras se verifica el token no se muestra nada: evita que
              parpadee "Iniciar sesión" a alguien que sí tiene sesión. */}
          {loading ? null : user ? (
            <>
              {isAdmin && (
                <Link href="/admin" className="text-neutral-500 hover:text-current">
                  Administrar
                </Link>
              )}
              <span className="text-neutral-500">{user.email}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-neutral-300 px-3 py-1.5 hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
              >
                Salir
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-neutral-500 hover:text-current">
                Iniciar sesión
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-neutral-900 px-3 py-1.5 text-white hover:bg-neutral-700 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
              >
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
