import { Redirect } from 'expo-router';

// Later this page will check GET /me and choose:
// login, first-time setup, or the Home map.
export default function Index() {
  return <Redirect href="/login" />;
}