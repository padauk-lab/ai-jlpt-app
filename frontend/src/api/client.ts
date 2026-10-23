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

// What a refresh attempt ended with.
// 'ok': new tokens saved. 'expired': the refresh token is no longer valid (401), so log in again.
// ApiError: the server had another problem (500, 429, no network); the user stays logged in.
type RefreshResult = 'ok' | 'expired' | ApiError;

// Only one refresh at a time, even if several requests get 401 together.
let refreshing: Promise<RefreshResult> | null = null;

async function refreshTokens(): Promise<RefreshResult> {
  const refresh = await tokens.refresh();
  if (!refresh) return 'expired';
  let res: Response;
  try {
    res = await send('/auth/refresh', { method: 'POST', body: { refresh_token: refresh }, auth: false });
  } catch (error) {
    return error as ApiError; // no network: keep the tokens and try again later
  }
  if (res.status === 401) {
    await tokens.clear(); // only a 401 means the login itself is over
    return 'expired';
  }
  if (!res.ok) return toError(res);
  await tokens.save(await res.json());
  return 'ok';
}

// Sends a request and returns the JSON body. When the access token has expired (401),
// it quietly gets a new one (#7) and tries once more, as the contract describes.
export async function request<T>(path: string, options: Options = {}): Promise<T> {
  let res = await send(path, options);

  if (res.status === 401 && options.auth !== false) {
    refreshing ??= refreshTokens().finally(() => {
      refreshing = null;
    });
    const result = await refreshing;
    if (result === 'ok') res = await send(path, options);
    else if (result !== 'expired') throw result; // e.g. 500 or 429: show that problem, don't log out
  }

  if (!res.ok) throw await toError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
