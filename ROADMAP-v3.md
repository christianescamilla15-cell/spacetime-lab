# Spacetime Lab — Roadmap v3 (Frontend Sprint)

**Inicio:** 2026-04-29
**Objetivo:** Llevar `spacetime-lab.vercel.app` de "stub Schwarzschild" a producto interactivo que cubra los 8 módulos físicos shipped en v0.1 → v2.1.
**Hipótesis:** El bottleneck a 100★ / contributors / arXiv no es más física (ya hay 655 tests, 15 notebooks), sino visibilidad. Lo shareable son visualizaciones interactivas, no notebooks estáticos.
**Duración total:** 6 semanas (v2.5 → v3.0).

---

## Estado real previo a este sprint

**Backend (FastAPI):**
- 3 endpoints Schwarzschild ✅ (`/properties`, `/tensor`, `/effective_potential`)
- `/api/available` lista 5 métricas — **4 marcadas `available: false` aunque YA EXISTEN en el package** (Kerr v0.3, BTZ v1.3, AdS v0.7, Reissner-Nordström sigue deferred desde Phase 2)
- CORS abierto

**Frontend (React + Vite):**
- `App.jsx`: Schwarzschild card + sliders + SVG visual + roadmap preview (~480 LOC)
- `EffectivePotential.jsx`: V_eff(r) interactivo, sliders M+L+particle_type, SVG plot ~486 LOC
- Stack: React 18.3.1 + Vite 5.4 + react-dom. Cero Three.js, cero KaTeX, cero Plotly, cero router
- Phase status en `App.jsx` desactualizado: marca Phase 1 "current" y resto "planned" — realmente todo Phase 1-9 + v1.x + v2.x está done

**Cobertura visual del codebase Python (qué % de los módulos tienen UI):**

| Módulo Python | Shipped | Backend API | Frontend UI |
|---|---|---|---|
| `metrics.Schwarzschild` | v0.1 | ✅ 3 endpoints | ✅ App.jsx |
| `metrics.Kerr` | v0.3 | ❌ | ❌ |
| `metrics.AdS` | v0.7 | ❌ | ❌ |
| `metrics.BTZ` | v0.8 / v1.3 | ❌ | ❌ |
| `diagrams.penrose` (matplotlib) | v0.2 | ❌ | ❌ |
| `diagrams.render_svg/tikz` | v1.5 | ❌ | ❌ |
| `geodesics` (symplectic) | v0.3 | ❌ | ❌ |
| `horizons` (event/ISCO/shadow) | v0.4 | ⚠️ parcial | ⚠️ parcial |
| `waves.qnm` | v0.5 / v1.2 | ❌ | ❌ |
| `entropy` (von Neumann, Schmidt) | v0.6 | ❌ | ❌ |
| `holography.ryu_takayanagi` | v0.7 | ❌ | ❌ |
| `holography.btz` (rotating + static) | v0.8 / v1.3 | ❌ | ❌ |
| `holography.island` (Page curve) | v0.9 / v1.1 | ❌ | ❌ |
| `holography.qes` | v2.0 / v2.1 | ❌ | ❌ |
| `holography.replica` | v2.0 | ❌ | ❌ |
| `holography.minimal_surfaces` | v2.0 / v2.1 | ❌ | ❌ |

**Conclusión:** ~94% del valor físico del package no está expuesto en la web. Tu visitante de `spacetime-lab.vercel.app` ve 1/8 del lab.

---

## v2.5 — Backend catch-up + Frontend foundations (Semana 1, 2026-04-29 → 2026-05-05)

### Goals
- Backend expone endpoints para Kerr, BTZ, AdS (los 3 módulos métricos shipped sin API)
- Listado `/api/available` dice la verdad (todos `available: true`)
- Frontend con react-router (4 rutas mínimas)
- Frontend con KaTeX para fórmulas
- App.jsx phases actualizado al estado real
- Setup Three.js + react-three-fiber para v2.7

### Deliverables

**Backend (`backend/app/routes/`):**
- [ ] `kerr.py` — endpoints: `/api/metrics/kerr/properties` (M, a/M → ISCO prograde/retrógrado, ergosphere, horizons r±)
- [ ] `kerr.py` — `/api/metrics/kerr/effective_potential` (massive equatorial)
- [ ] `kerr.py` — `/api/metrics/kerr/shadow` (Bardeen 1973 generator wrapper)
- [ ] `holography.py` — `/api/holography/page_curve/eternal` (Phase 9 wrapper)
- [ ] `holography.py` — `/api/holography/page_curve/evaporating` (v1.1 wrapper)
- [ ] `holography.py` — `/api/holography/rt/strip` (RT strip area for AdS)
- [ ] `geodesics.py` — `/api/geodesics/integrate` (POST: initial state + params → trajectory points)
- [ ] Update `/api/available` (5 métricas → 9, todos los `available` correctos)
- [ ] Tests pytest para los 4 nuevos routers (smoke + un "happy path" cada uno)

**Frontend (`frontend/src/`):**
- [ ] Install deps: `react-router-dom`, `katex`, `react-katex`, `three`, `@react-three/fiber`, `@react-three/drei`
- [ ] `pages/` — Home, Schwarzschild (mover App.jsx aquí), Kerr (stub), Penrose (stub), Holography (stub)
- [ ] `components/Layout.jsx` — Nav bar con links a las 4 secciones físicas
- [ ] `components/Math.jsx` — wrapper KaTeX para fórmulas inline + block
- [ ] App.jsx → solo router setup
- [ ] Refactor `Phase status` para reflejar estado real (Phase 1-9 done, v1.x done, v2.x done)
- [ ] Footer agrega "v2.1 · 655 tests · 15 notebooks"

**Release:** v2.5.0 — fin de semana 1.
**Tests:** suite Python sigue 655 + 4-6 nuevos para los routers nuevos.

---

## v2.6 — Kerr Visualizer + Penrose interactivo (Semana 2, 2026-05-06 → 2026-05-12)

### Goals
- Página Kerr completa: sliders M, a/M, sliders L y E para órbitas
- Visualización SVG 2D de Kerr en plano ecuatorial: ergosphere + horizons r± + ISCO prograde + photon sphere prograde + ergosphere
- Página Penrose: reusa `render_svg` v1.5 (ya shipped) → muestra Minkowski + Schwarzschild + toggle entre kinds
- Pan/zoom en SVG Penrose
- Hover en regiones I-IV muestra etiqueta + LaTeX

### Deliverables

**Backend:**
- [ ] `penrose.py` — `/api/diagrams/penrose/{kind}` returns SVG string (Minkowski/Schwarzschild)
- [ ] Kerr orbit endpoint: `/api/metrics/kerr/circular_orbits` (M, a/M → ISCO+photon sphere prograde + retrógrado)

**Frontend:**
- [ ] `pages/Kerr.jsx` — completo, equivalente al nivel de `App.jsx` actual pero para Kerr
- [ ] `components/KerrEquatorialPlot.jsx` — SVG concentric circles para horizons + ergosphere shaded
- [ ] `components/KerrParameterCard.jsx` — sliders + read-out + KaTeX formula card
- [ ] `pages/Penrose.jsx` — fetch SVG del backend, inject en DOM, manejar pan/zoom con `react-zoom-pan-pinch`
- [ ] Tooltip al hover sobre region en Penrose (I, II, III, IV) con descripción

**Release:** v2.6.0 — fin de semana 2.

---

## v2.7 — Geodesic Explorer 3D (Semana 3-4, 2026-05-13 → 2026-05-26)

### Goals
- Three.js scene con Kerr ergosphere + horizons como meshes 3D (semi-transparentes)
- User clica en una posición inicial 3D + setea L, E, Carter → backend integra geodésica → animación de trayectoria 3D
- Reusa `geodesics` symplectic integrator existente vía nuevo POST endpoint
- Slider de tiempo para "scrub" la trayectoria
- Multiple geodesics simultaneous (max 5)
- Camera orbital con drei OrbitControls

### Deliverables

**Backend:**
- [ ] `geodesics.py` — `POST /api/geodesics/integrate` body: `{metric: "kerr", params: {M, a}, initial_state: {r, theta, phi, t, p_r, p_theta, p_phi, p_t}, t_max, n_steps}` → `{trajectory: [[t,r,theta,phi], ...], conserved: {E, L, Q}, residuals: {...}}`
- [ ] Smoke test que la integración converge a 2nd-order (Schwarzschild como caso límite a=0)

**Frontend:**
- [ ] `pages/Geodesics.jsx`
- [ ] `components/KerrScene3D.jsx` — Canvas con horizons + ergosphere meshes
- [ ] `components/GeodesicTrail.jsx` — line + animated point along trajectory
- [ ] `components/InitialStatePicker.jsx` — clic en scene 3D para setear (r, theta, phi)
- [ ] `components/PlaybackControls.jsx` — play/pause/scrub time slider
- [ ] Conservation diagnostics panel: Energy, L_z, Carter constant residuals (verde si <1e-6)

**Release:** v2.7.0 — fin de semana 4.

---

## v2.8 — Holography showcase (Semana 5, 2026-05-27 → 2026-06-02)

### Goals
- Página unificada de Page curve + RT
- Slider de tiempo para Page curve (eternal vs evaporating side-by-side)
- AdS_3 visualizer: Poincaré half-plane interactivo, drag intervals → muestra geodésico minimal RT en tiempo real
- Cardy formula side panel: `S = (c/3) log(L/ε)` calculado en vivo
- Comparación: hand-identified saddle vs QES finder vs replica

### Deliverables

**Backend:**
- [ ] `holography.py` — completar endpoints faltantes (qes, replica, minimal_surfaces)

**Frontend:**
- [ ] `pages/Holography.jsx`
- [ ] `components/PageCurvePlot.jsx` — Plotly o SVG curve, eternal+evaporating overlay
- [ ] `components/AdSPoincareViewer.jsx` — SVG, semicírculos draggables como intervalos, geodésica RT calculada
- [ ] `components/CardyPanel.jsx` — display `c, β, L, ε → S` con KaTeX
- [ ] `components/IslandComparisonTable.jsx` — 3 saddles side-by-side

**Release:** v2.8.0 — fin de semana 5.

---

## v3.0 — Polish + Launch (Semana 6, 2026-06-03 → 2026-06-09)

### Goals
- Documentación inline en cada página (KaTeX para todas las fórmulas, citas a Wald/MTW)
- Loading states + error boundaries en todas las páginas
- Mobile responsive (al menos legible, no perfecto)
- "Powered by Spacetime Lab" embed snippet (iframe-able URL)
- Screenshots para Twitter / Reddit / Hacker News
- Blog post de lanzamiento (markdown en `docs/launch.md`)
- arXiv abstract draft (markdown en `docs/arxiv-draft.md`)
- Update README con GIFs de las 4 páginas

### Deliverables
- [ ] CSS responsive (media queries en cada componente)
- [ ] `pages/_layouts/EmbedLayout.jsx` — versión sin nav para iframe
- [ ] Routes `/embed/schwarzschild`, `/embed/kerr`, `/embed/penrose`, `/embed/holography`
- [ ] `docs/launch-blog.md` (~1500 palabras)
- [ ] `docs/arxiv-draft.md` (~2000 palabras, formato JCAP / GRG)
- [ ] 4 screenshots PNG en `docs/screenshots/`
- [ ] 4 GIFs cortos (~10s cada uno) en `docs/gifs/`
- [ ] Update README hero con embed del Kerr visualizer
- [ ] CHANGELOG entry v3.0

**Release:** **v3.0.0** 🚀 — fin de semana 6.

### Launch checklist
- [ ] Submit a r/Physics
- [ ] Submit a r/PhysicsStudents
- [ ] Submit a Hacker News (Show HN)
- [ ] Tweet thread con 4 GIFs
- [ ] Post LinkedIn con paper draft
- [ ] Mail a 5 BH physicists pidiendo feedback (sin spam, lista corta)

---

## Métricas objetivo v3.0 vs estado actual

| Métrica | Hoy (v2.1) | Objetivo v3.0 | Cómo medirlo |
|---|---|---|---|
| GitHub stars | ~0 | 50-200 | shields.io badge |
| Tests Python | 655 | 670-700 | pytest -q |
| Tests Frontend | 0 | 30-50 | Vitest |
| Páginas web interactivas | 1 (Schwarzschild) | 4 + Home | live URL |
| Módulos físicos cubiertos en UI | 1/16 | 6-8/16 | tabla arriba |
| Tutoriales notebooks | 15 | 15 | sin cambio (foco web) |
| Backend endpoints | 5 | 15-20 | OpenAPI count |
| Visitantes web/semana | ~0 | 100-500 | Vercel Analytics |
| Embed views/semana | 0 | 20-100 | iframe analytics |
| arXiv preprint | no | draft listo | docs/arxiv-draft.md |

---

## Stack añadido en este sprint

```json
{
  "react-router-dom": "^6.x",
  "katex": "^0.16.x",
  "react-katex": "^3.x",
  "three": "^0.160.x",
  "@react-three/fiber": "^8.x",
  "@react-three/drei": "^9.x",
  "react-zoom-pan-pinch": "^3.x"
}
```

NO se agrega:
- ❌ Tailwind (rompe el CSS-in-JS existente)
- ❌ Plotly (SVG manual cubre los casos)
- ❌ Redux/Zustand (useState local basta)
- ❌ MkDocs (docs van inline en el frontend)

---

## Riesgos identificados

1. **Vite 5 → Vite 8** mencionado en CLAUDE.md pero `package.json` está en 5.4. Posible inconsistencia. Mantener Vite 5 hasta forzar upgrade.
2. **Three.js performance en mobile**: Kerr 3D con 5 trayectorias puede ser pesado. Plan B: solo desktop, mensaje "best on desktop" en mobile.
3. **Backend deploy en Render free tier**: spin-down después de 15 min idle. Considerar ping cron o subir a paid tier para v3.0.
4. **arXiv submission**: requiere endorser. Si no consigues uno, blog post + Hacker News es plan B.
5. **Embed CORS**: si terceros embeben en sus sites, necesitas CORS bien configurado y CSP headers.

---

## Lo que NO entra en este sprint (deferred a v3.1+)

- Reissner-Nordström, FLRW, de Sitter (Phase 2 deferred desde forever)
- Kerr-Newman (v1.2 deferred)
- Bilby/PyCBC integration con LIGO real (Phase 5 deferred)
- HRT covariante (v0.8 deferred)
- General apparent horizon finder dinámico (v0.4 deferred)
- JT+bath dynamical wrapper (v2.0 deferred)
- Two-parameter QES (v2.1 deferred)
- Curved boundary regions (v2.1 deferred)
- Numerical replica wormhole path integral (v2.1 deferred)

Estos siguen siendo válidos pero no aportan a "visibilidad". Entran cuando v3.0 tenga tracción y demanden capacidades específicas.
