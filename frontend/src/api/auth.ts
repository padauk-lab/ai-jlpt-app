import { ApiError, request } from './client';
import { tokens, type Tokens } from './tokens';
import type { AuthResponse, Me } from './types';

// #2 POST /auth/register
export async function register(email: string, username: string, password: string): Promise<Me> {
  const data = await request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: { email, username, password },
    auth: false,
  });
  await tokens.save(data);
  return data.user;
}

// #3 POST /auth/login
export async function login(email: string, password: string): Promise<Me> {
  const data = await request<AuthResponse>('/auth/login', { method: 'POST', body: { email, password }, auth: false });
  await tokens.save(data);
  return data.user;
}

// #1 GET /me  (null when nobody is logged in)
export async function getMe(): Promise<Me | null> {
  if (!(await tokens.refresh())) return null;
  try {
    return await request<Me>('/me');
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

// #35 POST /auth/logout  (the tokens are removed from this phone even if the server can't be reached)
export async function logout(): Promise<void> {
  const refresh = await tokens.refresh();
  try {
    if (refresh) await request<void>('/auth/logout', { method: 'POST', body: { refresh_token: refresh } });
  } finally {
    await tokens.clear();
  }
}

// #5 POST /auth/forgot-password  (always the same answer, registered email or not)
export async function forgotPassword(email: string): Promise<void> {
  await request<{ message: string }>('/auth/forgot-password', { method: 'POST', body: { email }, auth: false });
}

// #6 POST /auth/reset-password  (every device is signed out, so the user logs in again)
export async function resetPassword(email: string, code: string, newPassword: string): Promise<void> {
  await request<{ message: string }>('/auth/reset-password', {
    method: 'POST',
    body: { email, code, new_password: newPassword },
    auth: false,
  });
}

// #34 POST /auth/change-password  (other devices are signed out; this one keeps working with the new tokens)
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const data = await request<Tokens & { message: string }>('/auth/change-password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  });
  await tokens.save(data);
}
