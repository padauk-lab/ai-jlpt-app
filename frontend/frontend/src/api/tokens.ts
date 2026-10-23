import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Login tokens (contract "Login tokens"): kept in the phone's secure storage,
// never in plain storage. Web browsers have no secure storage, so on the web the
// tokens live only in memory: reloading the page means logging in again.

const ACCESS = 'kyugo.access_token';
const REFRESH = 'kyugo.refresh_token';

export type Tokens = { access_token: string; refresh_token: string };

// Web only: the tokens for as long as the page stays open.
const inMemory: Record<string, string> = {};

async function read(key: string): Promise<string | null> {
  if (Platform.OS === 'web') return inMemory[key] ?? null;
  return SecureStore.getItemAsync(key);
}

async function write(key: string, value: string | null): Promise<void> {
  if (Platform.OS === 'web') {
    if (value === null) delete inMemory[key];
    else inMemory[key] = value;
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
