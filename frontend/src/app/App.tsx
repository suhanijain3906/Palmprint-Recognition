import { RouterProvider } from 'react-router-dom'
import { router } from './router'

/** Root component: mounts the router inside the global providers. */
export function App() {
  return <RouterProvider router={router} />
}

export default App
