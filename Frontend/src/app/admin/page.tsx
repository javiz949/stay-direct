"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { errorMessage, useAuth } from "@/lib/auth";
import type { Amenity, PriceSuggestion } from "@/types/api";

// Las 16 alcaldías de CDMX. Van fijas aquí y no en un fetch a propósito: son
// geografía estable (no cambian) y crear una propiedad no debe depender de que
// otro servicio esté arriba. El backend valida de todos modos: si algún nombre
// no coincidiera con los del modelo, la sugerencia responde 422 con el motivo.
const BOROUGHS = [
  "Azcapotzalco",
  "Benito Juárez",
  "Coyoacán",
  "Cuajimalpa de Morelos",
  "Cuauhtémoc",
  "Gustavo A. Madero",
  "Iztacalco",
  "Iztapalapa",
  "La Magdalena Contreras",
  "Miguel Hidalgo",
  "Milpa Alta",
  "Tlalpan",
  "Tláhuac",
  "Venustiano Carranza",
  "Xochimilco",
  "Álvaro Obregón",
];

const PROPERTY_TYPES = ["departamento", "casa", "loft", "estudio"];

const inputStyle =
  "rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900";

export default function AdminPage() {
  const router = useRouter();
  const { user, loading, isAdmin } = useAuth();

  const [amenities, setAmenities] = useState<Amenity[]>([]);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [address, setAddress] = useState("");
  const [propertyType, setPropertyType] = useState("departamento");
  const [maxGuests, setMaxGuests] = useState(2);
  const [bedrooms, setBedrooms] = useState(1);
  const [bathrooms, setBathrooms] = useState(1);
  const [price, setPrice] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());

  // La sugerencia es un estado aparte del formulario: pedirla no crea nada.
  const [suggestion, setSuggestion] = useState<PriceSuggestion | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestError, setSuggestError] = useState<string | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listAmenities()
      .then((list) => {
        if (!cancelled) setAmenities(list);
      })
      .catch(() => {
        // Sin catálogo solo se pierden los checkboxes; el formulario sigue vivo.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleAmenity(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const selectedNames = amenities
    .filter((a) => selected.has(a.id))
    .map((a) => a.name);

  async function handleSuggest() {
    setSuggestError(null);
    setSuggesting(true);
    try {
      const result = await api.suggestPrice({
        accommodates: maxGuests,
        bedrooms,
        bathrooms,
        neighborhood,
        amenities: selectedNames,
      });
      setSuggestion(result);
    } catch (e) {
      setSuggestion(null);
      if (e instanceof ApiError && e.status === 503) {
        setSuggestError(
          "El servicio de precios no está disponible. Captura el precio manualmente.",
        );
      } else {
        setSuggestError(errorMessage(e));
      }
    } finally {
      setSuggesting(false);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitError(null);
    setSubmitting(true);
    try {
      const created = await api.createProperty({
        title,
        description,
        city: "Ciudad de México",
        neighborhood,
        address,
        property_type: propertyType,
        max_guests: maxGuests,
        bedrooms,
        bathrooms,
        price_per_night: price,
        amenity_ids: [...selected],
      });
      router.push(`/properties/${created.id}`);
    } catch (e) {
      setSubmitError(errorMessage(e));
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-2xl px-6 py-10">
        <p className="text-sm text-neutral-500">Cargando...</p>
      </main>
    );
  }

  // Doble candado: el backend ya exige rol admin en estas rutas; esto solo
  // evita mostrar un formulario que fallaría.
  if (!user || !isAdmin) {
    return (
      <main className="mx-auto w-full max-w-2xl px-6 py-10">
        <h1 className="text-2xl font-bold tracking-tight">Administrar</h1>
        <p className="mt-4 text-sm text-neutral-500">
          Esta sección es solo para administradores.{" "}
          <Link href="/login" className="underline hover:text-current">
            Inicia sesión
          </Link>{" "}
          con una cuenta de administrador.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-bold tracking-tight">Nueva propiedad</h1>
      <p className="mt-1 text-sm text-neutral-500">
        Publica una propiedad del portafolio. El precio lo decides tú; el
        sistema puede sugerirte uno según el mercado.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Título
          <input
            required
            maxLength={120}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={inputStyle}
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          Descripción
          <textarea
            required
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={inputStyle}
          />
        </label>

        <div className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Alcaldía
            <select
              required
              value={neighborhood}
              onChange={(e) => setNeighborhood(e.target.value)}
              className={inputStyle}
            >
              <option value="" disabled>
                Elige una
              </option>
              {BOROUGHS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Tipo
            <select
              value={propertyType}
              onChange={(e) => setPropertyType(e.target.value)}
              className={`${inputStyle} capitalize`}
            >
              {PROPERTY_TYPES.map((t) => (
                <option key={t} value={t} className="capitalize">
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="flex flex-col gap-1 text-sm">
          Dirección
          <input
            required
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Calle y número, colonia"
            className={inputStyle}
          />
        </label>

        <div className="grid grid-cols-3 gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Huéspedes
            <input
              type="number"
              required
              min={1}
              max={20}
              value={maxGuests}
              onChange={(e) => setMaxGuests(Number(e.target.value))}
              className={inputStyle}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Recámaras
            <input
              type="number"
              required
              min={0}
              max={20}
              value={bedrooms}
              onChange={(e) => setBedrooms(Number(e.target.value))}
              className={inputStyle}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Baños
            <input
              type="number"
              required
              min={0.5}
              max={20}
              step={0.5}
              value={bathrooms}
              onChange={(e) => setBathrooms(Number(e.target.value))}
              className={inputStyle}
            />
          </label>
        </div>

        {amenities.length > 0 && (
          <fieldset className="text-sm">
            <legend className="mb-2">Amenidades</legend>
            <div className="grid grid-cols-2 gap-2">
              {amenities.map((a) => (
                <label key={a.id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selected.has(a.id)}
                    onChange={() => toggleAmenity(a.id)}
                  />
                  {a.name}
                </label>
              ))}
            </div>
          </fieldset>
        )}

        <div className="rounded-xl border border-neutral-200 p-4 dark:border-neutral-800">
          <div className="flex items-center justify-between gap-4">
            <label className="flex flex-1 flex-col gap-1 text-sm">
              Precio por noche (MXN)
              <input
                type="number"
                required
                min={1}
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className={inputStyle}
              />
            </label>

            <button
              type="button"
              onClick={handleSuggest}
              disabled={suggesting || neighborhood === ""}
              className="mt-5 rounded-md border border-neutral-300 px-3 py-2 text-sm hover:bg-neutral-100 disabled:opacity-50 dark:border-neutral-700 dark:hover:bg-neutral-900"
            >
              {suggesting ? "Consultando..." : "Sugerir precio"}
            </button>
          </div>

          {suggestion && (
            <div className="mt-3 rounded-md bg-neutral-100 px-3 py-2 text-sm dark:bg-neutral-900">
              <p>
                Sugerido:{" "}
                <span className="font-semibold">
                  ${suggestion.suggested_price.toLocaleString("es-MX")}
                </span>{" "}
                <span className="text-neutral-500">
                  (rango ${suggestion.range_low.toLocaleString("es-MX")} – $
                  {suggestion.range_high.toLocaleString("es-MX")})
                </span>
              </p>
              {suggestion.served_by && (
                <p className="mt-1 text-xs text-neutral-500">
                  Atendió: {suggestion.served_by}
                </p>
              )}
              <button
                type="button"
                onClick={() => setPrice(String(suggestion.suggested_price))}
                className="mt-2 rounded-md border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-200 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                Usar este precio
              </button>
            </div>
          )}

          {suggestError && (
            <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              {suggestError}
            </p>
          )}
        </div>

        {submitError && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            {submitError}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-3 py-2 text-sm text-white hover:bg-neutral-700 disabled:opacity-50 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
        >
          {submitting ? "Publicando..." : "Publicar propiedad"}
        </button>
      </form>
    </main>
  );
}
