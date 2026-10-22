import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { ApiError } from '@/services/api/api-error';

import {
  fetchCommunities,
  type ApiCommunity,
} from '../api/communities-api';
import {
  beginDiscoverRefresh,
  completeDiscoverRefresh,
  failDiscoverRefresh,
  initialDiscoverQuerySnapshot,
  type DiscoverQuerySnapshot,
} from '../state/discover-query-state';

const PAGE_SIZE = 30;
const SEARCH_DEBOUNCE_MS = 250;

export function useDiscoverCommunities(query: string, topic?: string) {
  const normalizedQuery = query.trim();
  const queryKey = JSON.stringify([normalizedQuery, topic ?? null]);
  const [snapshot, setSnapshot] = useState<DiscoverQuerySnapshot>(
    initialDiscoverQuerySnapshot,
  );
  const [retryCount, setRetryCount] = useState(0);
  const initialRequest = useRef<AbortController | null>(null);
  const refreshRequest = useRef<AbortController | null>(null);
  const nextPageRequest = useRef<AbortController | null>(null);
  const isLoadingMoreRef = useRef(false);

  useEffect(() => {
    initialRequest.current?.abort();
    refreshRequest.current?.abort();
    nextPageRequest.current?.abort();
    isLoadingMoreRef.current = false;

    const controller = new AbortController();
    initialRequest.current = controller;
    setSnapshot({
      key: queryKey,
      status: 'loading',
      pages: [],
      error: null,
      isRefreshing: false,
      refreshError: null,
      isLoadingMore: false,
      loadingMoreError: null,
    });

    const timer = setTimeout(() => {
      void fetchCommunities({
        q: normalizedQuery || undefined,
        topic,
        limit: PAGE_SIZE,
        offset: 0,
        signal: controller.signal,
      })
        .then((page) => {
          if (!controller.signal.aborted) {
            setSnapshot({
              key: queryKey,
              status: 'success',
              pages: [page],
              error: null,
              isRefreshing: false,
              refreshError: null,
              isLoadingMore: false,
              loadingMoreError: null,
            });
          }
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }
          setSnapshot({
            key: queryKey,
            status: 'error',
            pages: [],
            error:
              error instanceof ApiError
                ? error
                : new ApiError('Could not load communities. Please try again.', 'network'),
            isRefreshing: false,
            refreshError: null,
            isLoadingMore: false,
            loadingMoreError: null,
          });
        });
    }, normalizedQuery ? SEARCH_DEBOUNCE_MS : 0);

    return () => {
      clearTimeout(timer);
      controller.abort();
      refreshRequest.current?.abort();
      if (initialRequest.current === controller) {
        initialRequest.current = null;
      }
      nextPageRequest.current?.abort();
    };
  }, [normalizedQuery, queryKey, retryCount, topic]);

  const retry = useCallback(() => {
    setRetryCount((count) => count + 1);
  }, []);

  const currentSnapshot =
    snapshot.key === queryKey
      ? snapshot
      : {
          ...initialDiscoverQuerySnapshot,
          key: queryKey,
        };

  const refresh = useCallback(async () => {
    if (currentSnapshot.status !== 'success' || refreshRequest.current) {
      return;
    }

    initialRequest.current?.abort();
    nextPageRequest.current?.abort();
    isLoadingMoreRef.current = false;

    const controller = new AbortController();
    refreshRequest.current = controller;
    setSnapshot((current) =>
      current.key === queryKey ? beginDiscoverRefresh(current) : current,
    );

    try {
      const page = await fetchCommunities({
        q: normalizedQuery || undefined,
        topic,
        limit: PAGE_SIZE,
        offset: 0,
        signal: controller.signal,
      });
      if (controller.signal.aborted) {
        return;
      }
      setSnapshot((current) =>
        current.key === queryKey ? completeDiscoverRefresh(current, page) : current,
      );
    } catch (error) {
      if (!controller.signal.aborted) {
        const refreshError =
          error instanceof ApiError
            ? error
            : new ApiError(
                'Could not refresh communities. Showing saved results.',
                'network',
              );
        setSnapshot((current) =>
          current.key === queryKey ? failDiscoverRefresh(current, refreshError) : current,
        );
      }
    } finally {
      if (refreshRequest.current === controller) {
        refreshRequest.current = null;
      }
    }
  }, [currentSnapshot.status, normalizedQuery, queryKey, topic]);

  const loadMore = useCallback(async () => {
    if (
      currentSnapshot.status !== 'success' ||
      refreshRequest.current !== null ||
      currentSnapshot.isRefreshing ||
      currentSnapshot.isLoadingMore ||
      isLoadingMoreRef.current
    ) {
      return;
    }

    const offset = currentSnapshot.pages.reduce((count, page) => count + page.items.length, 0);
    const total = currentSnapshot.pages.at(-1)?.total ?? 0;
    if (offset >= total) {
      return;
    }

    const controller = new AbortController();
    nextPageRequest.current?.abort();
    nextPageRequest.current = controller;
    isLoadingMoreRef.current = true;
    setSnapshot((current) =>
      current.key === queryKey
        ? { ...current, isLoadingMore: true, loadingMoreError: null }
        : current,
    );

    try {
      const page = await fetchCommunities({
        q: normalizedQuery || undefined,
        topic,
        limit: PAGE_SIZE,
        offset,
        signal: controller.signal,
      });
      if (controller.signal.aborted) {
        return;
      }
      setSnapshot((current) => {
        if (current.key !== queryKey) {
          return current;
        }
        if (current.pages.some((currentPage) => currentPage.offset === page.offset)) {
          return { ...current, isLoadingMore: false };
        }
        return {
          ...current,
          pages: [...current.pages, page],
          isLoadingMore: false,
          loadingMoreError: null,
        };
      });
    } catch (error) {
      if (!controller.signal.aborted) {
        setSnapshot((current) =>
          current.key === queryKey
            ? {
                ...current,
                isLoadingMore: false,
                loadingMoreError:
                  error instanceof ApiError
                    ? error
                    : new ApiError('Could not load more communities.', 'network'),
              }
            : current,
        );
      }
    } finally {
      isLoadingMoreRef.current = false;
      if (nextPageRequest.current === controller) {
        nextPageRequest.current = null;
      }
    }
  }, [currentSnapshot, normalizedQuery, queryKey, topic]);

  const retryLoadingMore = useCallback(() => {
    void loadMore();
  }, [loadMore]);

  const items: ApiCommunity[] = useMemo(
    () => currentSnapshot.pages.flatMap((page) => page.items),
    [currentSnapshot.pages],
  );
  const lastPage = currentSnapshot.pages.at(-1);

  return {
    items,
    total: lastPage?.total ?? 0,
    status: currentSnapshot.status,
    error: currentSnapshot.error,
    hasNextPage: items.length < (lastPage?.total ?? 0),
    isLoadingMore: currentSnapshot.isLoadingMore,
    loadingMoreError: currentSnapshot.loadingMoreError,
    isRefreshing: currentSnapshot.isRefreshing,
    refreshError: currentSnapshot.refreshError,
    retry,
    refresh,
    loadMore,
    retryLoadingMore,
  };
}
