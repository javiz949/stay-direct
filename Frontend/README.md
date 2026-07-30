# Frontend

Interfaz web de Stay Direct. Next.js (App Router) con TypeScript y Tailwind.

No contiene lógica de negocio: consulta la API del Backend y muestra los datos.

## Configuración

Copiar `.env.example` como `.env.local` y ajustar la URL del Backend:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Desarrollo

```bash
npm install
npm run dev
```

Queda en http://localhost:3000. Requiere el Backend corriendo en el puerto 8000.

## Estructura

```
src/
├── app/          # rutas (App Router de Next.js)
├── lib/api.ts    # cliente de la API: unico punto que llama al Backend
└── types/api.ts  # contratos TypeScript, espejo de los schemas de Pydantic
```
