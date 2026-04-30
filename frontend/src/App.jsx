/**
 * v2.5 router-only App.  All physics moved out into per-page components.
 * The previous monolithic App.jsx is preserved in git history; its
 * Schwarzschild content lives at `pages/Schwarzschild.jsx` and its
 * EffectivePotential is still imported there.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import EmbedLayout from './components/EmbedLayout'
import Home from './pages/Home'
import Schwarzschild from './pages/Schwarzschild'
import Kerr from './pages/Kerr'
import BTZ from './pages/BTZ'
import ReissnerNordstrom from './pages/ReissnerNordstrom'
import KerrNewman from './pages/KerrNewman'
import Geodesics from './pages/Geodesics'
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
          <Route path="btz" element={<BTZ />} />
          <Route path="reissner-nordstrom" element={<ReissnerNordstrom />} />
          <Route path="kerr-newman" element={<KerrNewman />} />
          <Route path="geodesics" element={<Geodesics />} />
          <Route path="penrose" element={<Penrose />} />
          <Route path="holography" element={<Holography />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        <Route path="/embed" element={<EmbedLayout />}>
          <Route path="schwarzschild" element={<Schwarzschild />} />
          <Route path="kerr" element={<Kerr />} />
          <Route path="btz" element={<BTZ />} />
          <Route path="reissner-nordstrom" element={<ReissnerNordstrom />} />
          <Route path="kerr-newman" element={<KerrNewman />} />
          <Route path="geodesics" element={<Geodesics />} />
          <Route path="penrose" element={<Penrose />} />
          <Route path="holography" element={<Holography />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
