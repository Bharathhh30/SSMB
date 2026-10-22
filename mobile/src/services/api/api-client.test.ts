import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from './api-error';

const fetchMock = vi.fn<typeof fetch>();
let getJson: typeof import('./api-client').getJson;

beforeAll(async () => {
  vi.stubEnv('EXPO_PUBLIC_API_BASE_URL', 'https://api.example.test/api/v1///');
  vi.stubEnv('EXPO_PUBLIC_APP_ENV', 'development');
  vi.stubGlobal('fetch', fetchMock);
  ({ getJson } = await import('./api-client'));
});

beforeEach(() => {
  fetchMock.mockReset();
  vi.useRealTimers();
});

afterAll(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('getJson', () => {
  it('uses the configured API base URL and requests JSON', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ready: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(getJson('/health/ready')).resolves.toEqual({ ready: true });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/api/v1/health/ready',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it('converts HTTP errors to safe, typed API errors', async () => {
    const requestId = '9b6e0918532c45c8b8ff3e4a7264ab12';
    fetchMock.mockResolvedValue(
      new Response('private upstream details', {
        status: 503,
        headers: { 'X-Request-ID': requestId },
      }),
    );

    await expect(getJson('/communities')).rejects.toMatchObject({
      kind: 'http',
      message: 'The community service is having trouble. Please try again.',
      requestId,
      status: 503,
    });
  });

  it('reports malformed JSON as a response error', async () => {
    const requestId = 'c4f0a50f5ae14a699fb776610abea035';
    fetchMock.mockResolvedValue(
      new Response('not-json', {
        status: 200,
        headers: { 'X-Request-ID': requestId },
      }),
    );

    await expect(getJson('/communities')).rejects.toMatchObject({
      kind: 'response',
      message: 'The server returned a response we could not read.',
      requestId,
    });
  });

  it('ignores malformed request IDs supplied by an unexpected server', async () => {
    fetchMock.mockResolvedValue(
      new Response('upstream failure', {
        status: 500,
        headers: { 'X-Request-ID': 'invalid-id-with-user-data' },
      }),
    );

    await expect(getJson('/communities')).rejects.toMatchObject({
      kind: 'http',
      requestId: undefined,
    });
  });

  it('maps network failures without exposing the underlying exception', async () => {
    fetchMock.mockRejectedValue(new TypeError('private DNS failure details'));

    await expect(getJson('/communities')).rejects.toMatchObject({
      kind: 'network',
      message: 'Could not reach the community server. Check the API URL and your connection.',
    });
  });

  it('distinguishes a request timeout from a network failure', async () => {
    vi.useFakeTimers();
    fetchMock.mockImplementation(
      (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener(
            'abort',
            () => reject(new DOMException('The request was aborted.', 'AbortError')),
            { once: true },
          );
        }),
    );

    const request = getJson('/communities');
    const timedOutRequest = expect(request).rejects.toMatchObject({
      kind: 'timeout',
      message: 'The server took too long to respond. Check your connection and retry.',
    });
    await vi.advanceTimersByTimeAsync(12_000);
    await timedOutRequest;
  });

  it('preserves caller-initiated cancellation', async () => {
    fetchMock.mockImplementation(
      (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener(
            'abort',
            () => reject(new DOMException('The request was aborted.', 'AbortError')),
            { once: true },
          );
        }),
    );

    const controller = new AbortController();
    const request = getJson('/communities', { signal: controller.signal });
    controller.abort();

    await expect(request).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('uses ApiError for all expected request failures', async () => {
    fetchMock.mockResolvedValue(new Response('upstream failure', { status: 500 }));

    await expect(getJson('/communities')).rejects.toBeInstanceOf(ApiError);
  });
});
