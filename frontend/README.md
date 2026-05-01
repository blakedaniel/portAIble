# portAIble Frontend

Nuxt 4 + Nuxt UI client for the portAIble backend.

## Dev

```bash
npm install
npm run dev                      # http://localhost:3000 by default
# or pick a free port:
npm run dev -- --port 3050
```

The backend must be reachable at `NUXT_PUBLIC_API_BASE` (default `http://localhost:8001`).

> **Note**: 3000/3001/3002 are pre-allowed for CORS. If you pick another port, append it to
> `FRONTEND_ORIGINS=http://localhost:3000,...` in the backend `.env` so CORS matches.

## Generated API client

Once the backend is running, dump its OpenAPI spec and regenerate the typed client:

```bash
curl http://localhost:8001/openapi.json -o ../openapi.json
npm run gen:api
```
