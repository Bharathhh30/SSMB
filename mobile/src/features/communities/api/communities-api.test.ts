import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/services/api/api-error';
import { getJson } from '@/services/api/api-client';

import {
  fetchCommunities,
  fetchCommunityTopics,
  parseCommunity,
  parseCommunityTopicList,
  type ApiCommunity,
} from './communities-api';

vi.mock('@/services/api/api-client', () => ({
  getJson: vi.fn(),
}));

const getJsonMock = vi.mocked(getJson);

const validCommunity: ApiCommunity = {
  id: 'community-1',
  slug: 'gate-quant-lab',
  name: 'GATE Quant Lab',
  topic: 'Exam prep',
  description: 'Focused problem solving.',
  access_type: 'open',
  expires_at: null,
  created_at: '2026-01-15T12:00:00Z',
};

describe('parseCommunity', () => {
  it('accepts a valid public community response', () => {
    expect(parseCommunity(validCommunity)).toEqual(validCommunity);
  });

  it.each([
    ['unknown access type', { access_type: 'members_only' }],
    ['invalid creation timestamp', { created_at: 'not-a-date' }],
    ['invalid expiry timestamp', { expires_at: 'not-a-date' }],
    ['missing slug', { slug: undefined }],
  ])('rejects a response with %s', (_description, overrides) => {
    expect(() => parseCommunity({ ...validCommunity, ...overrides })).toThrow(ApiError);
  });
});

describe('community topics', () => {
  beforeEach(() => {
    getJsonMock.mockReset();
  });

  it('parses a list of non-empty topic names', () => {
    expect(parseCommunityTopicList({ items: ['Exam prep', 'Technology'] })).toEqual({
      items: ['Exam prep', 'Technology'],
    });
  });

  it.each([
    null,
    { items: 'Technology' },
    { items: ['Technology', ' '] },
    { items: ['Technology', null] },
  ])('rejects malformed topic payloads', (payload) => {
    expect(() => parseCommunityTopicList(payload)).toThrow(ApiError);
  });

  it('requests the topics endpoint and forwards cancellation', async () => {
    const signal = new AbortController().signal;
    getJsonMock.mockResolvedValue({ items: ['Exam prep', 'Technology'] });

    await expect(fetchCommunityTopics(signal)).resolves.toEqual(['Exam prep', 'Technology']);
    expect(getJsonMock).toHaveBeenCalledWith('/topics', { signal });
  });
});

describe('fetchCommunities', () => {
  beforeEach(() => {
    getJsonMock.mockReset();
  });

  it('trims search text, encodes filters, and forwards the abort signal', async () => {
    const signal = new AbortController().signal;
    getJsonMock.mockResolvedValue({
      items: [validCommunity],
      total: 1,
      limit: 30,
      offset: 30,
    });

    const page = await fetchCommunities({
      q: '  GATE quant  ',
      topic: 'Exam prep',
      limit: 30,
      offset: 30,
      signal,
    });

    expect(getJsonMock).toHaveBeenCalledWith(
      '/communities?limit=30&offset=30&q=GATE+quant&topic=Exam+prep',
      { signal },
    );
    expect(page.items).toEqual([validCommunity]);
    expect(page.total).toBe(1);
  });

  it('omits blank search text and rejects malformed community records', async () => {
    getJsonMock.mockResolvedValue({
      items: [{ ...validCommunity, access_type: 'members_only' }],
      total: 1,
      limit: 30,
      offset: 0,
    });

    await expect(
      fetchCommunities({ q: '   ', limit: 30, offset: 0 }),
    ).rejects.toMatchObject({ kind: 'response' });

    expect(getJsonMock).toHaveBeenCalledWith('/communities?limit=30&offset=0', {
      signal: undefined,
    });
  });

  it('rejects invalid pagination metadata in the list response', async () => {
    getJsonMock.mockResolvedValue({
      items: [validCommunity],
      total: '1',
      limit: 30,
      offset: 0,
    });

    await expect(fetchCommunities({ limit: 30, offset: 0 })).rejects.toMatchObject({
      kind: 'response',
    });
  });
});
