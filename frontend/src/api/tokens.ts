import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Login tokens (contract "Login tokens"): kept in the phone's secure storage,
// never in plain storage. Web browsers have no secure storage, so on the web
// (only used while developing) they are kept in localStorage instead.

const ACCESS = 'kyugo.access_token';
const REFRESH = 'kyugo.refresh_token';

export type Tokens = { access_token: string; refresh_token: string };

async function read(key: string): Promise<string | null> {
  if (Platform.OS === 'web') return globalThis.localStorage?.getItem(key) ?? null;
  return SecureStore.getItemAsync(key);
}

async function write(key: string, value: string | null): Promise<void> {
  if (Platform.OS === 'web') {
    if (value === null) globalThis.localStorage?.removeItem(key);
    else globalThis.localStorage?.setItem(key, value);
    return;
  }
  if (value === null) await SecureStore.deleteItemAsync(key);
  else await SecureStore.setItemAsync(key, value);
}

export const tokens = {
  access: () => read(ACCESS),
  refresh: () => read(REFRESH),
  async save(pair: Tokens) {
    await write(ACCESS, pair.access_token);
    await write(REFRESH, pair.refresh_token);
  },
  async clear() {
    await write(ACCESS, null);
    await write(REFRESH, null);
  },
};
