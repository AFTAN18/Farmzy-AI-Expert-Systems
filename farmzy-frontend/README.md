# FARMZY Frontend (Next.js 14)

## Setup

1. Install dependencies:

```bash
npm install
```

2. Configure environment:

```bash
cp .env.local.example .env.local
```

3. Run development server:

```bash
npm run dev
```

The app expects backend API at `NEXT_PUBLIC_API_BASE_URL` and WebSocket at `NEXT_PUBLIC_WS_URL`.
