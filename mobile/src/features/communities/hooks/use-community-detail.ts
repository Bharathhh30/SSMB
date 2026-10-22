import { useCallback, useEffect, useState } from 'react';

import { ApiError } from '@/services/api/api-error';

import { fetchCommunity, type ApiCommunity } from '../api/communities-api';

type DetailSnapshot = {
  slug: string;
  status: 'loading' | 'success' | 'error';
  community: ApiCommunity | null;
  error: ApiError | null;
};

const initialSnapshot: DetailSnapshot = {
  slug: '',
  status: 'loading',
  community: null,
  error: null,
};

export function useCommunityDetail(slug: string) {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setSnapshot({
      slug,
      status: 'loading',
      community: null,
      error: null,
    });

    if (!slug) {
      setSnapshot({
        slug,
        status: 'error',
        community: null,
        error: new ApiError('This community link is incomplete.', 'response'),
      });
      return () => controller.abort();
    }

    void fetchCommunity(slug, controller.signal)
      .then((community) => {
        if (!controller.signal.aborted) {
          setSnapshot({ slug, status: 'success', community, error: null });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setSnapshot({
            slug,
            status: 'error',
            community: null,
            error:
              error instanceof ApiError
                ? error
                : new ApiError('Could not load this community. Please try again.', 'network'),
          });
        }
      });

    return () => controller.abort();
  }, [retryCount, slug]);

  const retry = useCallback(() => {
    setRetryCount((count) => count + 1);
  }, []);

  const currentSnapshot =
    snapshot.slug === slug
      ? snapshot
      : {
          ...initialSnapshot,
          slug,
        };

  return {
    status: currentSnapshot.status,
    community: currentSnapshot.community,
    error: currentSnapshot.error,
    retry,
  };
}
