import Link from "next/link";

import { api, ApiError } from "@/lib/api";
import type { Property } from "@/types/api";

/**
 * Catálogo público de propiedades.
 *
 * Es un Server Component: la función es async y hace el fetch antes de mandar el
 * HTML al navegador. No lleva estado de carga ni useEffect porque el usuario
 * recibe la página ya renderizada con los datos.
 */
export default async function Home() {
  let properties: Property[] = [];
  let error: string | null = null;

  try {
    properties = await api.listProperties();
  } catch (e) {
    // Si el Backend está caído la página debe explicarlo, no reventar.
    error = e instanceof ApiError ? e.message : "No se pudo conectar con el servidor";
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">Propiedades</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Reserva directa, sin comisiones de intermediarios
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <p className="font-medium">No se pudieron cargar las propiedades</p>
          <p className="mt-1 text-red-700">{error}</p>
          <p className="mt-2 text-xs text-red-600">
            Verifica que el Backend esté corriendo en {process.env.NEXT_PUBLIC_API_URL}
          </p>
        </div>
      )}

      {!error && properties.length === 0 && (
        <p className="text-sm text-neutral-500">Todavía no hay propiedades publicadas.</p>
      )}

      {properties.length > 0 && (
        <>
          <p className="mb-4 text-sm text-neutral-500">
            {properties.length} propiedades disponibles
          </p>

          <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {properties.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </ul>
        </>
      )}
    </main>
  );
}

function PropertyCard({ property }: { property: Property }) {
  return (
    <li className="flex flex-col rounded-xl border border-neutral-200 p-5 transition-shadow hover:shadow-md dark:border-neutral-800">
      <h2 className="font-semibold leading-snug">
        <Link href={`/propiedades/${property.id}`} className="hover:underline">
          {property.title}
        </Link>
      </h2>

      <p className="mt-1 text-sm text-neutral-500">
        {property.neighborhood}, {property.city}
      </p>

      <p className="mt-3 line-clamp-2 text-sm text-neutral-600">{property.description}</p>

      <dl className="mt-4 flex gap-4 text-xs text-neutral-500">
        <div>
          <dt className="sr-only">Huéspedes</dt>
          <dd>{property.max_guests} huéspedes</dd>
        </div>
        <div>
          <dt className="sr-only">Recámaras</dt>
          <dd>
            {property.bedrooms} {property.bedrooms === 1 ? "recámara" : "recámaras"}
          </dd>
        </div>
        <div>
          <dt className="sr-only">Baños</dt>
          <dd>
            {property.bathrooms} {property.bathrooms === 1 ? "baño" : "baños"}
          </dd>
        </div>
      </dl>

      {property.amenities.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {property.amenities.slice(0, 4).map((amenity) => (
            <li
              key={amenity.id}
              className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600"
            >
              {amenity.name}
            </li>
          ))}
          {property.amenities.length > 4 && (
            <li className="px-1 py-0.5 text-xs text-neutral-400">
              +{property.amenities.length - 4}
            </li>
          )}
        </ul>
      )}

      {/* price_per_night viene como texto (Decimal de Pydantic): hay que
          convertirlo a número para formatearlo con separador de miles. */}
      <p className="mt-auto pt-4 text-sm">
        <span className="text-lg font-semibold">
          ${Number(property.price_per_night).toLocaleString("es-MX")}
        </span>
        <span className="text-neutral-500"> / noche</span>
      </p>
    </li>
  );
}
