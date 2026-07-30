"use client";

import "react-day-picker/style.css";

import { DayPicker, type DateRange, type Matcher } from "react-day-picker";
import { es } from "react-day-picker/locale";

import type { UnavailableRange } from "@/types/api";

/**
 * Convierte "YYYY-MM-DD" a una fecha local.
 *
 * A propósito no se usa new Date("2026-07-30"): ese formato se interpreta como
 * UTC medianoche, y en México (UTC-6) eso cae el día anterior a las 18:00, así
 * que el calendario mostraría los días corridos.
 */
export function parseDate(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** El inverso, para mandar la fecha al Backend. toISOString() tampoco sirve
 *  aquí: convierte a UTC y por la tarde ya devuelve el día siguiente. */
export function formatDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function startOfToday(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

// Noches ya tomadas. Se declara el tipo con from y to obligatorios (DateRange
// los permite undefined) para poder leerlos sin comprobar en cada uso.
type BookedRange = { from: Date; to: Date };

/**
 * Traduce las reservas a las noches que ya están tomadas.
 *
 * Una reserva ocupa las noches [check_in, check_out): el día de salida el
 * huésped se va, así que otro puede llegar ese mismo día. Por eso el rango
 * termina un día antes del check_out.
 */
function bookedRanges(unavailable: UnavailableRange[]): BookedRange[] {
  const ranges: BookedRange[] = [];

  for (const range of unavailable) {
    const from = parseDate(range.check_in);
    const to = parseDate(range.check_out);
    to.setDate(to.getDate() - 1);
    // En una reserva de una noche from y to caen el mismo día: sigue siendo válido.
    if (to >= from) ranges.push({ from, to });
  }

  return ranges;
}

/** Arranque de la primera reserva posterior a `from`, o null si no hay ninguna. */
function nextBookedStart(from: Date, booked: BookedRange[]): Date | null {
  const later = booked.filter((range) => range.from > from);
  if (later.length === 0) return null;
  return new Date(Math.min(...later.map((range) => range.from.getTime())));
}

/**
 * Qué días se bloquean, que depende de qué se está eligiendo en ese momento.
 *
 * Al elegir la LLEGADA no sirve ninguna noche ocupada. Al elegir la SALIDA sí
 * sirve el día en que arranca la siguiente reserva: esa mañana el huésped
 * anterior se va, así que es una salida válida. Lo único prohibido es brincar
 * por encima de esa reserva.
 */
function disabledDays(
  selected: DateRange | undefined,
  booked: BookedRange[],
): Matcher[] {
  const from = selected?.from;

  // Todavía falta la salida si ya hay llegada pero no una salida distinta. Ojo
  // con el segundo caso: react-day-picker deja to = from en el primer clic, y
  // eso son 0 noches, o sea que la reserva sigue incompleta. Compararlos, y no
  // solo mirar si to existe, es lo que distingue los dos momentos.
  const pickingCheckOut =
    from !== undefined &&
    (selected?.to === undefined || selected.to.getTime() === from.getTime());

  // Sin llegada, o con el rango ya completo: el siguiente clic es una llegada.
  if (!pickingCheckOut) {
    return [{ before: startOfToday() }, ...booked];
  }

  // Eligiendo la salida: de la llegada en adelante, hasta el arranque de la
  // siguiente reserva inclusive.
  const limit = nextBookedStart(from, booked);
  const matchers: Matcher[] = [{ before: from }];
  if (limit) matchers.push({ after: limit });
  return matchers;
}

export function AvailabilityCalendar({
  unavailable,
  selected,
  onSelect,
}: {
  unavailable: UnavailableRange[];
  selected: DateRange | undefined;
  onSelect: (range: DateRange | undefined) => void;
}) {
  const booked = bookedRanges(unavailable);

  return (
    <DayPicker
      mode="range"
      locale={es}
      selected={selected}
      onSelect={onSelect}
      disabled={disabledDays(selected, booked)}
      // Modificador propio solo para lo reservado. Sirve para tacharlo y así
      // distinguirlo de los días pasados, que están bloqueados por otra razón.
      // Es fijo: el tachado no debe moverse mientras se elige.
      modifiers={{ booked }}
      modifiersClassNames={{ booked: "rdp-booked" }}
      // Red de seguridad: si un rango llegara a incluir un día bloqueado, la
      // selección se reinicia en vez de mandarle un traslape al Backend.
      excludeDisabled
      startMonth={startOfToday()}
      // La clase se monta junto a rdp-root y sirve para subir la especificidad
      // de los estilos propios en globals.css. Ver el comentario de allá.
      className="booking-calendar"
      // Los 44px que trae por defecto no caben en la columna de 320px.
      style={
        {
          "--rdp-day-width": "38px",
          "--rdp-day-height": "38px",
          "--rdp-day_button-width": "36px",
          "--rdp-day_button-height": "36px",
        } as React.CSSProperties
      }
    />
  );
}
