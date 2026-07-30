"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { errorMessage, useAuth } from "@/lib/auth";

/** Fecha de hoy en formato YYYY-MM-DD, que es lo que espera <input type="date">
 *  y también el Backend. Se usa como mínimo: no se reservan fechas pasadas. */
function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function nightsBetween(checkIn: string, checkOut: string): number {
  if (!checkIn || !checkOut) return 0;
  const ms = new Date(checkOut).getTime() - new Date(checkIn).getTime();
  return Math.max(0, Math.round(ms / 86_400_000));
}

export function BookingForm({
  propertyId,
  pricePerNight,
  maxGuests,
}: {
  propertyId: number;
  pricePerNight: number;
  maxGuests: number;
}) {
  const router = useRouter();
  const { user, loading } = useAuth();

  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const nights = nightsBetween(checkIn, checkOut);

  // Estimación solo para mostrar. El total real lo calcula el Backend: el
  // frontend no hace lógica de negocio.
  const estimate = nights * pricePerNight;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const booking = await api.createBooking({
        property_id: propertyId,
        check_in: checkIn,
        check_out: checkOut,
      });
      router.push(`/reservas?nueva=${booking.id}`);
    } catch (e) {
      // 409 es el caso interesante: el Backend rechazó por traslape de fechas.
      if (e instanceof ApiError && e.status === 409) {
        setError("Esas fechas ya están ocupadas. Prueba con otras.");
      } else {
        setError(errorMessage(e));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <aside className="h-fit rounded-xl border border-neutral-200 p-5 dark:border-neutral-800">
      <p className="text-sm">
        <span className="text-xl font-semibold">
          ${pricePerNight.toLocaleString("es-MX")}
        </span>
        <span className="text-neutral-500"> / noche</span>
      </p>
      <p className="mt-1 text-xs text-neutral-500">Hasta {maxGuests} huéspedes</p>

      {loading ? null : !user ? (
        <p className="mt-5 text-sm text-neutral-500">
          <Link href="/login" className="underline hover:text-current">
            Inicia sesión
          </Link>{" "}
          para reservar.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Llegada
            <input
              type="date"
              required
              min={today()}
              value={checkIn}
              onChange={(e) => setCheckIn(e.target.value)}
              className="rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Salida
            <input
              type="date"
              required
              // La salida debe ser posterior a la llegada; el Backend lo valida
              // igual, esto solo evita el viaje innecesario.
              min={checkIn || today()}
              value={checkOut}
              onChange={(e) => setCheckOut(e.target.value)}
              className="rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
            />
          </label>

          {nights > 0 && (
            <p className="flex justify-between border-t border-neutral-200 pt-3 text-sm dark:border-neutral-800">
              <span className="text-neutral-500">
                {nights} {nights === 1 ? "noche" : "noches"}
              </span>
              <span className="font-medium">${estimate.toLocaleString("es-MX")}</span>
            </p>
          )}

          {error && (
            <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || nights === 0}
            className="rounded-md bg-neutral-900 px-3 py-2 text-sm text-white hover:bg-neutral-700 disabled:opacity-50 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            {submitting ? "Reservando..." : "Reservar"}
          </button>
        </form>
      )}
    </aside>
  );
}
