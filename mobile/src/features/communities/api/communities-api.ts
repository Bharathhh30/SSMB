import { getJson } from '@/services/api/api-client';
import { ApiError } from '@/services/api/api-error';

export type ApiCommunity = {
  id: string;
  slug: string;
  name: string;
  topic: string;
  description: string;
  access_type: 'open' | 'invite_only';
  expires_at: string | null;
  created_at: string;
};

export type CommunityPage = {
  items: ApiCommunity[];
  total: number;
  limit: number;
  offset: number;
};

type CommunityQuery = {
  q?: string;
  topic?: string;
  limit: number;
  offset: number;
  signal?: AbortSignal;
};

export type CommunityTopicList = {
  items: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isDateOrNull(value: unknown): value is string | null {
  return (
    value === null ||
    (typeof value === 'string' && Number.isFinite(Date.parse(value)))
  );
}

export function parseCommunity(value: unknown): ApiCommunity {
  if (
    !isRecord(value) ||
    typeof value.id !== 'string' ||
    typeof value.slug !== 'string' ||
    typeof value.name !== 'string' ||
    typeof value.topic !== 'string' ||
    typeof value.description !== 'string' ||
    (value.access_type !== 'open' && value.access_type !== 'invite_only') ||
    !isDateOrNull(value.expires_at) ||
    typeof value.created_at !== 'string' ||
    !Number.isFinite(Date.parse(value.created_at))
  ) {
    throw new ApiError('The server returned community data in an unexpected format.', 'response');
  }

  return {
    id: value.id,
    slug: value.slug,
    name: value.name,
    topic: value.topic,
    description: value.description,
    access_type: value.access_type,
    expires_at: value.expires_at,
    created_at: value.created_at,
  };
}

function parsePage(value: unknown): CommunityPage {
  if (
    !isRecord(value) ||
    !Array.isArray(value.items) ||
    !Number.isInteger(value.total) ||
    !Number.isInteger(value.limit) ||
    !Number.isInteger(value.offset)
  ) {
    throw new ApiError('The server returned community results in an unexpected format.', 'response');
  }

  return {
    items: value.items.map(parseCommunity),
    total: value.total as number,
    limit: value.limit as number,
    offset: value.offset as number,
  };
}

export function parseCommunityTopicList(value: unknown): CommunityTopicList {
  if (
    !isRecord(value) ||
    !Array.isArray(value.items) ||
    !value.items.every((item) => typeof item === 'string' && item.trim().length > 0)
  ) {
    throw new ApiError('The server returned community topics in an unexpected format.', 'response');
  }

  return { items: value.items as string[] };
}

export async function fetchCommunityTopics(signal?: AbortSignal): Promise<string[]> {
  const payload = await getJson('/topics', { signal });
  return parseCommunityTopicList(payload).items;
}

export async function fetchCommunities({
  q,
  topic,
  limit,
  offset,
  signal,
}: CommunityQuery): Promise<CommunityPage> {
  const parameters = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (q?.trim()) {
    parameters.set('q', q.trim());
  }
  if (topic) {
    parameters.set('topic', topic);
  }

  const payload = await getJson(`/communities?${parameters.toString()}`, { signal });
  return parsePage(payload);
}

export async function fetchCommunity(slug: string, signal?: AbortSignal): Promise<ApiCommunity> {
  const payload = await getJson(`/communities/${encodeURIComponent(slug)}`, { signal });
  return parseCommunity(payload);
}
