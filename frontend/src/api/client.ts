import { API_URL } from './config';
import { tokens } from './tokens';

// Every error from the backend has the contract's shape:
// { "error": { "code": "...", "message": "...", "fields": { ... } } }
export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string>;
  retryAfter?: number; // seconds, for 429 "too many requests"

  constructor(status: number, code: string, message: string, fields?: Record<string, string>, retryAfter?: number) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.retryAfter = retryAfter;
  }
}

type Options = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  auth?: boolean; // send the access token (default true)
};

async function send(path: string, { method = 'GET', body, auth = true }: Options): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const access = await tokens.access();
    if (access) headers.Authorization = `Bearer ${access}`;
  }
  try {
    return await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // No answer at all: no internet, or the backend is not running.
    throw new ApiError(0, 'network_error', 'Cannot reach the server.');
  }
}

async function toError(res: Response): Promise<ApiError> {
  let code = 'server_error';
  let message = 'Something went wrong.';
  let fields: Record<string, string> | undefined;
  try {
    const data = await res.json();
    code = data?.error?.code ?? code;
    message = data?.error?.message ?? message;
    fields = data?.error?.fields;
  } catch {
    // not JSON; keep the defaults
  }
  const retry = Number(res.headers.get('Retry-After'));
  return new ApiError(res.status, code, message, fields, Number.isFinite(retry) && retry > 0 ? retry : undefined);
}

// Only one refresh at a time, even if several requests get 401 together.
let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh = await tokens.refresh();
  if (!refresh) return false;
  const res = await send('/auth/refresh', { method: 'POST', body: { refresh_token: refresh }, auth: false });
  if (!res.ok) {
    await tokens.clear(); // the refresh token is no longer valid: log in again
    return false;
  }
  await tokens.save(await res.json());
  return true;
}

// Sends a request and returns the JSON body. When the access token has expired (401),
// it quietly gets a new one (#7) and tries once more, as the contract describes.
export async function request<T>(path: string, options: Options = {}): Promise<T> {
  let res = await send(path, options);

  if (res.status === 401 && options.auth !== false) {
    refreshing ??= refreshTokens().finally(() => {
      refreshing = null;
    });
    if (await refreshing) res = await send(path, options);
  }

  if (!res.ok) throw await toError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
