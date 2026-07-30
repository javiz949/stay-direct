import Link from "next/link";
import { notFound } from "next/navigation";

import { BookingForm } from "@/components/booking-form";
import { api, ApiError } from "@/lib/api";
import type { Property } from "@/types/api";

/**
 * Detalle de una propiedad, con el formulario de reserva.
 *
 * En Next.js 16 `params` es una Promise: hay que await-earla antes de leer el id.
 */
export default async function PropertyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const propertyId = Number(id);
  if (!Number.isInteger(propertyId)) notFound();

  // El try envuelve solo el fetch, no el JSX: React no renderiza en este punto,
  // así que un try alrededor del JSX no atraparía errores de renderizado.
  let property: Property;
  try {
    property = await api.getProperty(propertyId);
  } catch (e) {
    // El Backend responde 404 tanto si no existe como si está desactivada.
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link href="/" className="text-sm text-neutral-500 hover:text-current">
        ← Volver al catálogo
      </Link>

      <header className="mt-6">
        <h1 className="text-3xl font-bold tracking-tight">{property.title}</h1>
        <p className="mt-1 text-neutral-500">
          {property.address}, {property.neighborhood}, {property.city}
        </p>
      </header>

      <div className="mt-8 grid gap-10 md:grid-cols-[1fr_320px]">
        <div>
          <p className="text-neutral-700 dark:text-neutral-300">{property.description}</p>

          <dl className="mt-6 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Detail label="Tipo" value={property.property_type} />
            <Detail label="Huéspedes" value={String(property.max_guests)} />
            <Detail label="Recámaras" value={String(property.bedrooms)} />
            <Detail label="Baños" value={String(property.bathrooms)} />
          </dl>

          {property.amenities.length > 0 && (
            <section className="mt-8">
              <h2 className="text-sm font-semibold">Amenidades</h2>
              <ul className="mt-3 flex flex-wrap gap-2">
                {property.amenities.map((amenity) => (
                  <li
                    key={amenity.id}
                    className="rounded-full bg-neutral-100 px-3 py-1 text-sm text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                  >
                    {amenity.name}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* El formulario es Client Component: necesita estado, sesión y manejar
            la respuesta del Backend. */}
        <BookingForm
          propertyId={property.id}
          pricePerNight={Number(property.price_per_night)}
          maxGuests={property.max_guests}
        />
      </div>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-neutral-500">{label}</dt>
      <dd className="mt-0.5 font-medium capitalize">{value}</dd>
    </div>
  );
}
