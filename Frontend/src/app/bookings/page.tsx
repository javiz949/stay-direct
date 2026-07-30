"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { errorMessage, useAuth } from "@/lib/auth";
import type { Booking, BookingStatus } from "@/types/api";

const STATUS_LABEL: Record<BookingStatus, string> = {
  pending: "Pendiente",
  confirmed: "Confirmada",
  cancelled: "Cancelada",
};

const STATUS_STYLE: Record<BookingStatus, string> = {
  pending: "bg-amber-100 text-amber-800",
  confirmed: "bg-green-100 text-green-800",
  cancelled: "bg-neutral-200 text-neutral-600",
};

export default function BookingsPage() {
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  // Id que viene del formulario de reserva, para resaltar la recién creada.
  const newBookingId = Number(searchParams.get("new"));

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      // El Backend devuelve solo las del usuario del token: el frontend no
      // filtra nada, la autorización vive del lado del servidor.
      setBookings(await api.listMyBookings());
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;

    // Todo el setState va después del await: llamarlo de forma síncrona en el
    // cuerpo del efecto dispara renders en cascada.
    async function loadIfLoggedIn() {
      if (user) await load();
    }

    loadIfLoggedIn().then(() => setLoading(false));
  }, [authLoading, user, load]);

  async function handleCancel(id: number) {
    try {
      await api.cancelBooking(id);
      await load(); // recarga para ver el nuevo estado
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (authLoading || loading) {
    return (
      <main className="mx-auto w-full max-w-3xl px-6 py-10">
        <p className="text-sm text-neutral-500">Cargando...</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="mx-auto w-full max-w-3xl px-6 py-10">
        <h1 className="text-2xl font-bold tracking-tight">Mis reservas</h1>
        <p className="mt-4 text-sm text-neutral-500">
          <Link href="/login" className="underline hover:text-current">
            Inicia sesión
          </Link>{" "}
          para ver tus reservas.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-10">
      <h1 className="text-2xl font-bold tracking-tight">Mis reservas</h1>

      {error && (
        <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}

      {bookings.length === 0 && !error && (
        <p className="mt-4 text-sm text-neutral-500">
          Todavía no tienes reservas.{" "}
          <Link href="/" className="underline hover:text-current">
            Ver propiedades
          </Link>
        </p>
      )}

      <ul className="mt-6 flex flex-col gap-3">
        {bookings.map((booking) => (
          <li
            key={booking.id}
            className={`rounded-xl border p-5 ${
              booking.id === newBookingId
                ? "border-green-300 bg-green-50/40"
                : "border-neutral-200 dark:border-neutral-800"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-neutral-500">Reserva #{booking.id}</p>
                <Link
                  href={`/properties/${booking.property_id}`}
                  className="text-sm underline hover:text-current"
                >
                  Ver propiedad
                </Link>
                <p className="mt-2 text-sm">
                  {booking.check_in} → {booking.check_out}
                </p>
                <p className="mt-1 text-sm font-medium">
                  ${Number(booking.total_price).toLocaleString("es-MX")}
                </p>
              </div>

              <div className="flex flex-col items-end gap-2">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[booking.status]}`}
                >
                  {STATUS_LABEL[booking.status]}
                </span>

                {booking.status !== "cancelled" && (
                  <button
                    type="button"
                    onClick={() => handleCancel(booking.id)}
                    className="rounded-md border border-neutral-300 px-3 py-1.5 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
                  >
                    Cancelar
                  </button>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
