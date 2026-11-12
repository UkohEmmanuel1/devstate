# DevState frontend

The dashboard is a Next.js App Router application written in TypeScript. Tailwind CSS 4 provides styling and Lucide React provides icons.

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3000. Set `NEXT_PUBLIC_DEVSTATE_API` in `.env.local` if Django is not running at `http://127.0.0.1:8000/api`.

Run the Django API separately; see `backend/README.md`. The UI uses live Django endpoints when reachable and labels itself Demo mode while using sample data otherwise.
