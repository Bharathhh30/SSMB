import { useCallback, useEffect, useState } from 'react';

import { ApiError } from '@/services/api/api-error';

import { fetchCommunityTopics } from '../api/communities-api';

type TopicSnapshot = {
  status: 'loading' | 'success' | 'error';
  topics: string[];
  error: ApiError | null;
};

const initialSnapshot: TopicSnapshot = {
  status: 'loading',
  topics: [],
  error: null,
};

export function useCommunityTopics() {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setSnapshot(initialSnapshot);

    void fetchCommunityTopics(controller.signal)
      .then((topics) => {
        if (!controller.signal.aborted) {
          setSnapshot({ status: 'success', topics, error: null });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setSnapshot({
            status: 'error',
            topics: [],
            error:
              error instanceof ApiError
                ? error
                : new ApiError('Could not load community topics. Please try again.', 'network'),
          });
        }
      });

    return () => controller.abort();
  }, [retryCount]);

  const retry = useCallback(() => {
    setRetryCount((count) => count + 1);
  }, []);

  return { ...snapshot, retry };
}
