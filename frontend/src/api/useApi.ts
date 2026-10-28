import { useEffect, useRef, useState } from 'react';

export type ApiState<T> =
  { status: 'loading' } | { status: 'error'; message: string } | { status: 'success'; data: T };

/** Runs `load` whenever `key` changes (key must encode all of load's inputs). */
export function useApi<T>(key: string, load: (signal: AbortSignal) => Promise<T>): ApiState<T> {
  const loadRef = useRef(load);
  const [state, setState] = useState<{ key: string; value: ApiState<T> } | null>(null);

  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    const controller = new AbortController();
    loadRef
      .current(controller.signal)
      .then((data) => setState({ key, value: { status: 'success', data } }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          const message = error instanceof Error ? error.message : String(error);
          setState({ key, value: { status: 'error', message } });
        }
      });
    return () => controller.abort();
  }, [key]);

  return state?.key === key ? state.value : { status: 'loading' };
}
