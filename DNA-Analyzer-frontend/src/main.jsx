import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* BrowserRouter wires the app up to the browser's native History API
        (pushState/popState) so routes, the back/forward buttons, and
        refreshes on a given URL all behave correctly. */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
