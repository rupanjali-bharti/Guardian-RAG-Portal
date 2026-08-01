const DEFAULT_API_BASE_URL = import.meta.env.PROD
  ? 'https://auditgaurd.onrender.com'
  : 'http://127.0.0.1:5001';

function normalizeBaseUrl(value = '') {
  const trimmedValue = `${value || DEFAULT_API_BASE_URL}`.trim();
  if (!trimmedValue) return DEFAULT_API_BASE_URL;
  return trimmedValue.replace(/\/+$/, '').replace(/\/api$/, '');
}

function sanitizePath(path = '') {
  const normalizedPath = `${path || ''}`.trim().replace(/^\/+/, '').replace(/\/+$/, '');
  return normalizedPath.replace(/^api\/?/, '');
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);

export function API_ENDPOINT(path = '') {
  const cleanedPath = sanitizePath(path);

  if (!cleanedPath) {
    return `${API_BASE_URL}/api`;
  }

  return `${API_BASE_URL}/api/${cleanedPath}`;
}

function isRetryableError(error) {
  return error?.name === 'AbortError' || error?.message?.includes('Failed to fetch') || error?.message?.includes('NetworkError');
}

export async function apiRequest(path = '', options = {}) {
  const {
    method = 'GET',
    body,
    headers,
    timeoutMs = 30000,
    retries = 1,
    ...restOptions
  } = options;

  const requestHeaders = new Headers(headers || {});
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  let requestBody = body;

  if (!isFormData && requestBody !== undefined && requestBody !== null && typeof requestBody === 'object' && !(requestBody instanceof Blob) && !(requestBody instanceof ArrayBuffer)) {
    if (!requestHeaders.has('Content-Type')) {
      requestHeaders.set('Content-Type', 'application/json');
    }
    if (typeof requestBody === 'string') {
      requestBody = requestBody;
    } else {
      requestBody = JSON.stringify(requestBody);
    }
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(API_ENDPOINT(path), {
      method,
      body: requestBody,
      headers: requestHeaders,
      signal: controller.signal,
      ...restOptions,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(errorText || `Request failed with status ${response.status}`);
    }

    return response;
  } catch (error) {
    if (retries > 0 && isRetryableError(error)) {
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
      return apiRequest(path, { ...options, retries: retries - 1 });
    }

    if (error?.name === 'AbortError') {
      throw new Error('The backend is taking too long to respond. It may be waking up from sleep.');
    }

    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}
