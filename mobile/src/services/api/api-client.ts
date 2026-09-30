import { getApiBaseUrl } from '@/config/env';

import { ApiError } from './api-error';

const REQUEST_TIMEOUT_MS = 12_000;

type JsonRequestOptions = {
  signal?: AbortSignal;
};

function getErrorMessage(status: number): string {
  if (status >= 500) {
    return 'The community service is having trouble. Please try again.';
  }
  return `The request could not be completed (HTTP ${status}).`;
}

export async function getJson(
  path: string,
  { signal }: JsonRequestOptions = {},
): Promise<unknown> {
  let baseUrl: string;
  try {
    baseUrl = getApiBaseUrl();
  } catch (error) {
    throw new ApiError(
      error instanceof Error ? error.message : 'The API URL is not configured.',
      'configuration',
    );
  }

  const timeoutController = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    timeoutController.abort();
  }, REQUEST_TIMEOUT_MS);
  const abortRequest = () => timeoutController.abort();

  signal?.addEventListener('abort', abortRequest, { once: true });
  if (signal?.aborted) {
    abortRequest();
  }

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: { Accept: 'application/json' },
      signal: timeoutController.signal,
    });

    if (!response.ok) {
      throw new ApiError(getErrorMessage(response.status), 'http', response.status);
    }

    try {
      return await response.json();
    } catch {
      throw new ApiError('The server returned a response we could not read.', 'response');
    }
  } catch (error) {
    if (signal?.aborted) {
      throw error;
    }
    if (timedOut) {
      throw new ApiError(
        'The server took too long to respond. Check your connection and retry.',
        'timeout',
      );
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      'Could not reach the community server. Check the API URL and your connection.',
      'network',
    );
  } finally {
    clearTimeout(timeoutId);
    signal?.removeEventListener('abort', abortRequest);
  }
}
