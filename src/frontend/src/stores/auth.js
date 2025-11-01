import { writable } from 'svelte/store';

const isBrowser = typeof window !== 'undefined';
const storedToken = isBrowser ? localStorage.getItem('auth_token') : null;
const storedUser = isBrowser ? localStorage.getItem('auth_user') : null;

export const token = writable(storedToken || null);
export const user = writable(storedUser ? JSON.parse(storedUser) : null);
export const isAuthenticated = writable(!!storedToken);

// Subscribe to token changes and update localStorage
token.subscribe(value => {
  if (isBrowser) {
    if (value) {
      localStorage.setItem('auth_token', value);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
});

// Subscribe to user changes and update localStorage
user.subscribe(value => {
  if (isBrowser) {
    if (value) {
      localStorage.setItem('auth_user', JSON.stringify(value));
    } else {
      localStorage.removeItem('auth_user');
    }
  }
});

export function login(authToken, userData) {
  token.set(authToken);
  user.set(userData);
  isAuthenticated.set(true);
}

export function logout() {
  token.set(null);
  user.set(null);
  isAuthenticated.set(false);
}
