import { describe, expect, it } from 'vitest';

import { ApiError } from '@/services/api/api-error';

import type { CommunityPage } from '../api/communities-api';
import {
  beginDiscoverRefresh,
  completeDiscoverRefresh,
  failDiscoverRefresh,
  type DiscoverQuerySnapshot,
} from './discover-query-state';

const currentPage: CommunityPage = {
  items: [
    {
      id: 'circle-1',
      slug: 'circle-one',
      name: 'Circle One',
      topic: 'Learning',
      description: 'A community for learning.',
      access_type: 'open',
      expires_at: null,
      created_at: '2026-09-30T10:00:00Z',
    },
  ],
  total: 1,
  limit: 30,
  offset: 0,
};

const nextPage: CommunityPage = {
  ...currentPage,
  items: [
    {
      ...currentPage.items[0],
      id: 'circle-2',
      slug: 'circle-two',
      name: 'Circle Two',
    },
  ],
  total: 2,
};

const snapshot: DiscoverQuerySnapshot = {
  key: '["",null]',
  status: 'success',
  pages: [currentPage],
  error: null,
  isRefreshing: false,
  refreshError: null,
  isLoadingMore: true,
  loadingMoreError: null,
};

describe('discover refresh state', () => {
  it('starts refresh without dropping existing results', () => {
    const refreshing = beginDiscoverRefresh(snapshot);

    expect(refreshing.status).toBe('success');
    expect(refreshing.pages).toEqual([currentPage]);
    expect(refreshing.isRefreshing).toBe(true);
    expect(refreshing.isLoadingMore).toBe(false);
    expect(refreshing.loadingMoreError).toBeNull();
  });

  it('replaces the first page and clears transient errors after refresh succeeds', () => {
    const currentWithError = {
      ...snapshot,
      refreshError: new ApiError('Previous refresh failed.', 'network'),
    };

    expect(completeDiscoverRefresh(currentWithError, nextPage)).toMatchObject({
      status: 'success',
      pages: [nextPage],
      error: null,
      isRefreshing: false,
      refreshError: null,
      isLoadingMore: false,
      loadingMoreError: null,
    });
  });

  it('keeps the loaded page available after refresh fails', () => {
    const error = new ApiError('Refresh failed.', 'network');
    const failed = failDiscoverRefresh(beginDiscoverRefresh(snapshot), error);

    expect(failed.status).toBe('success');
    expect(failed.pages).toEqual([currentPage]);
    expect(failed.isRefreshing).toBe(false);
    expect(failed.refreshError).toBe(error);
  });
});
