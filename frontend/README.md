# Frontend (Expo)

Owner: LMHP. Screens and UI for iOS, Android and web.

## Run
```bash
cd frontend
npm install
npx expo start
```
Press w for web, or scan the QR code with Expo Go.

## Backend
Local API: http://localhost:8000/api/v1
Start it from the repo root with docker compose up.

## Folders
- src/app: screens (Expo Router)
- src/api: the only place that talks to the backend (fake data in src/api/fake)
- src/theme: colors, fonts, spacing
- src/components: shared UI parts