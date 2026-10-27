import { useCallback, useEffect, useRef, useState } from 'react'
import { describeError } from '../services/apiClient'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}


export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
): AsyncState<TResult> & { run: (...args: TArgs) => Promise<TResult | null>; reset: () => void } {
  const [state, setState] = useState<AsyncState<TResult>>({
    data: null,
    loading: false,
    error: null,
  })
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const run = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setState((prev) => ({ ...prev, loading: true, error: null }))
      try {
        const result = await action(...args)
        if (mounted.current) setState({ data: result, loading: false, error: null })
        return result
      } catch (err) {
        if (mounted.current) {
          setState({ data: null, loading: false, error: describeError(err) })
        }
        return null
      }
    },
    [action],
  )

  const reset = useCallback(() => setState({ data: null, loading: false, error: null }), [])

  return { ...state, run, reset }
}

/** Fetch data once when the component mounts (or when the key changes). */
export function useAsyncData<T>(
  loader: () => Promise<T>,
  deps: unknown[] = [],
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  })
  const loaderRef = useRef(loader)
  loaderRef.current = loader
  const [reloadToken, setReloadToken] = useState(0)
  // A serialised key keeps the dependency list a static array literal, which
  // the exhaustive-deps rule is able to verify.
  const depsKey = JSON.stringify(deps ?? [])

  useEffect(() => {
    let active = true
    setState((prev) => ({ ...prev, loading: true, error: null }))
    loaderRef
      .current()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null })
      })
      .catch((err) => {
        if (active) setState({ data: null, loading: false, error: describeError(err) })
      })
    return () => {
      active = false
    }
  }, [depsKey, reloadToken])

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  return { ...state, reload }
}
