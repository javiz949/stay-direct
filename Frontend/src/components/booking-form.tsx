"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { DateRange } from "react-day-picker";

import { AvailabilityCalendar, formatDate } from "@/components/availability-calendar";
import { api, ApiError } from "@/lib/api";
import { errorMessage, useAuth } from "@/lib/auth";
import type { UnavailableRange } from "@/types/api";

export function BookingForm({
  propertyId,
  pricePerNight,
  maxGuests,
  unavailable,
}: {
  propertyId: number;
  pricePerNight: number;
  maxGuests: number;
  unavailable: UnavailableRange[];
}) {
  const router = useRouter();
  const { user, loading, isAdmin } = useAuth();

  // Un solo estado para las dos fechas: el calendario las devuelve juntas.
  const [range, setRange] = useState<DateRange | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Ambas fechas son medianoche local, así que la resta da días exactos.
  const nights =
    range?.from && range.to
      ? Math.round((range.to.getTime() - range.from.getTime()) / 86_400_000)
      : 0;

  // Estimación solo para mostrar. El total real lo calcula el Backend: el
  // frontend no hace lógica de negocio.
  const estimate = nights * pricePerNight;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    // Con un solo clic en el calendario todavía no hay rango que enviar.
    if (!range?.from || !range.to) return;

    setError(null);
    setSubmitting(true);

    try {
      const booking = await api.createBooking({
        property_id: propertyId,
        check_in: formatDate(range.from),
        check_out: formatDate(range.to),
      });
      router.push(`/bookings?new=${booking.id}`);
    } catch (e) {
      // El 409 se sigue manejando aunque el calendario bloquee las fechas: entre
      // que cargó la página y este clic, alguien más pudo reservar esos días.
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
      ) : isAdmin ? (
        // El Backend responde 403 al admin. Se avisa aquí en vez de mostrar un
        // formulario que fallaría siempre: el admin es dueño del portafolio.
        <p className="mt-5 rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-500 dark:border-neutral-700">
          Estás en modo administrador. Las reservas son para huéspedes.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
          <AvailabilityCalendar
            unavailable={unavailable}
            selected={range}
            onSelect={setRange}
          />

          <div className="flex flex-col gap-1 text-sm">
            <p className="flex justify-between">
              <span className="text-neutral-500">Llegada</span>
              <span className="font-medium">
                {range?.from ? formatDate(range.from) : "—"}
              </span>
            </p>
            <p className="flex justify-between">
              <span className="text-neutral-500">Salida</span>
              <span className="font-medium">
                {nights > 0 && range?.to ? formatDate(range.to) : "—"}
              </span>
            </p>
          </div>

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
