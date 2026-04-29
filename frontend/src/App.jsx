/**
 * v2.5 router-only App.  All physics moved out into per-page components.
 * The previous monolithic App.jsx is preserved in git history; its
 * Schwarzschild content lives at `pages/Schwarzschild.jsx` and its
 * EffectivePotential is still imported there.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Schwarzschild from './pages/Schwarzschild'
import Kerr from './pages/Kerr'
import Penrose from './pages/Penrose'
import Holography from './pages/Holography'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="schwarzschild" element={<Schwarzschild />} />
          <Route path="kerr" element={<Kerr />} />
          <Route path="penrose" element={<Penrose />} />
          <Route path="holography" element={<Holography />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
