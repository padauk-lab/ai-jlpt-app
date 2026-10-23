// Where the backend lives. Each teammate can change it in frontend/.env:
//   EXPO_PUBLIC_API_URL=http://192.168.1.23:8000/api/v1   (your Mac's address, for testing on a phone)
// Only put addresses here, never secrets: anything starting with EXPO_PUBLIC_ is visible inside the app.
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
