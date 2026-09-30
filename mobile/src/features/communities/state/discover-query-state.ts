import { ApiError } from '@/services/api/api-error';

import type { CommunityPage } from '../api/communities-api';

export type DiscoverQuerySnapshot = {
  key: string;
  status: 'loading' | 'success' | 'error';
  pages: CommunityPage[];
  error: ApiError | null;
  isRefreshing: boolean;
  refreshError: ApiError | null;
  isLoadingMore: boolean;
  loadingMoreError: ApiError | null;
};

export const initialDiscoverQuerySnapshot: DiscoverQuerySnapshot = {
  key: '',
  status: 'loading',
  pages: [],
  error: null,
  isRefreshing: false,
  refreshError: null,
  isLoadingMore: false,
  loadingMoreError: null,
};

export function beginDiscoverRefresh(
  snapshot: DiscoverQuerySnapshot,
): DiscoverQuerySnapshot {
  return {
    ...snapshot,
    isRefreshing: true,
    refreshError: null,
    isLoadingMore: false,
    loadingMoreError: null,
  };
}

export function completeDiscoverRefresh(
  snapshot: DiscoverQuerySnapshot,
  page: CommunityPage,
): DiscoverQuerySnapshot {
  return {
    ...snapshot,
    status: 'success',
    pages: [page],
    error: null,
    isRefreshing: false,
    refreshError: null,
    isLoadingMore: false,
    loadingMoreError: null,
  };
}

export function failDiscoverRefresh(
  snapshot: DiscoverQuerySnapshot,
  error: ApiError,
): DiscoverQuerySnapshot {
  return {
    ...snapshot,
    isRefreshing: false,
    refreshError: error,
  };
}
