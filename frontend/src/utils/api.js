const DEFAULT_API_BASE_URL = import.meta.env.PROD
  ? 'https://auditgaurd.onrender.com'
  : 'http://127.0.0.1:5001';

function normalizeBaseUrl(value = '') {
  const trimmedValue = `${value || DEFAULT_API_BASE_URL}`.trim();
  if (!trimmedValue) return DEFAULT_API_BASE_URL;
  return trimmedValue.replace(/\/+$/, '').replace(/\/api$/, '');
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);

export function API_ENDPOINT(path = '') {
  const normalizedPath = `${path || ''}`.trim().replace(/^\/+/, '').replace(/\/+$/, '');
  const cleanedPath = normalizedPath.replace(/^api\/?/, '');

  if (!cleanedPath) {
    return `${API_BASE_URL}/api`;
  }

  return `${API_BASE_URL}/api/${cleanedPath}`;
}
