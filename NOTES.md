# Dev notes

Things I figured out the hard way, kept in chronological-ish order. Not tutorials, not specs. Just the kind of stuff I would have wanted someone else to have written down.

If you find a contradiction between this file and the actual code, the code wins.

---

## Float roundoff almost killed Kerr-Newman cosmic censorship

Test was failing on `KerrNewman(M=1, a=0.6, Q=0.8)`. Should be exactly extremal: `0.6² + 0.8² = 1.0`. Test asserted `is_extremal == True`. It was raising ValueError in the constructor.

Why: in IEEE 754, `0.6**2 + 0.8**2 = 1.0000000000000002`. My check was `if a**2 + Q**2 > M**2: raise`. The two extra bits of mantissa rounding push it over.

Fix: `+ 1e-12` tolerance in the comparison, plus `max(disc, 0.0)` clamp on the discriminant in `_disc()` and `ergosphere()` so the sqrt doesn't NaN. The integer-input case (M=1, a=0.6, Q=0.8 from the test) now correctly hits the extremal branch.

Generalisation: any GR code that computes "is this exactly extremal" with `==` is wrong. Always tolerance.

---

## Symplectic integrator: E and L_z drift = exact zero

Took me a while to internalise this. In Boyer-Lindquist Kerr, `t` and `phi` are cyclic coordinates. Their conjugate momenta `E = -p_t` and `L_z = p_phi` are exact constants of the geodesic motion.

For the implicit-midpoint integrator (or any symplectic integrator), these are preserved to machine precision. Not "small drift". Not "O(h²)". *Zero* drift, except for `~1e-16` machine epsilon noise.

Carter's constant Q is different. It's a hidden constant of motion (Killing tensor, not Killing vector), so the integrator doesn't preserve it exactly. It drifts at O(h²) per step, exactly as the symplectic geometry predicts.

The `ConservationPanel` component shows all four diagnostics. Watching E and L_z stick at exactly the initial value while Q drifts in the predicted way is the prettiest debug session of the project.

When I first built this I thought there was a bug because the drift was too small. There wasn't.

---

## Penrose region tracking is harder than I expected

The Penrose page renders Schwarzschild as a four-region diagram. It works for static rendering. Adding a geodesic overlay only works for region I (our universe).

I want to track a particle that crosses the future event horizon into region II. This needs Kruskal-Szekeres coordinates, which means re-integrating the geodesic in (U, V) instead of (t, r). The overlay code does the (t, r) → (U, V) projection at the end, but only for samples that haven't crossed the horizon (r > 2M).

Multi-day rebuild to do properly. Parked.

---

## Render Blueprint failed because of `-e ../`

First Render deploy for the v3.2 launch failed at build. Backend `requirements.txt` had `-e ../` to install the local `spacetime_lab` package. Works locally because the relative path resolves. Fails on Render because pip runs from `backend/` but `..` doesn't resolve to the repo root in their sandbox the way it does locally.

Fix in commit `0350ee3`: split the build command in `render.yaml` into two steps:
```yaml
buildCommand: "pip install -r backend/requirements.txt && pip install ."
```
Removed `-e ../` from `requirements.txt`. Render now installs the requirements first (from `backend/`), then `pip install .` from the repo root installs the local package.

Also pinned `scipy<1.14` because newer versions try to source-build on Render free tier and OOM.

If you ever fork this and your deploy fails: the next layer of fixes is `uv` instead of pip (faster resolver) or Render Starter ($7/mo) for cached builds.

---

## Vercel Vite env vars are baked at build, not runtime

Spent half an hour confused why the deployed frontend was hitting `localhost:8000`. The `VITE_API_URL` was set in Vercel's env var page, but the bundle still had the old value.

Vite inlines `import.meta.env.VITE_*` at build time. Setting the env var in the dashboard does nothing until you redeploy. AND the redeploy needs cache OFF, otherwise it just re-uploads the previous bundle.

Sequence that actually works:
1. Set `VITE_API_URL` in Vercel → Settings → Environment Variables (all 3 envs).
2. Deployments → ⋯ → Redeploy → uncheck "Use existing build cache".
3. Wait 60-90 s.
4. Verify by curling the deployed JS: `curl <vercel-url>/assets/index-*.js | grep onrender.com` — should show the API URL.

---

## scipy.optimize.brentq vs. fsolve for ISCO

For Reissner-Nordström, ISCO is the point where dL²/dr changes sign. I first wrote it with `fsolve` on `d²V/dr²`. Precision floor of about 8e-5, way worse than the 1e-12 the test wanted.

Two issues stacked:
1. `d²V/dr²` numerically requires three potential evaluations near the candidate r. Cancellation kills precision.
2. `fsolve` is multidimensional Newton; for a 1D rootfind it's overkill and converges to the noise floor.

Fix: use `brentq` (1D bracketed rootfind, much more precise) on the analytical numerator polynomial `dL²_num(r) = u'v - uv'` where `u = M·r³ - Q²·r²` and `v = r² - 3Mr + 2Q²`. The polynomial form has no cancellation. Hits 1e-15 trivially.

Generalisation: if your numerical method has a precision floor that's bigger than `eps × condition number`, you're using the wrong method. Switch.

---

## The r/Physics post got removed under the "AI/LLM-generated content" rule

Posted on 2026-04-30. Mod removed it ~1h later citing the AI/LLM content rule. The hostile first reply ("vibe coded, zero market research") drew mod attention.

I documented the full post-mortem in `docs/launch-postmortem-2026-04-30.md`. Two takeaways:

1. The bar for "doesn't read as LLM output by a hostile reader" is different from "the project is real". You have to clear both, separately.
2. Polished prose + lots of citations + clean structure is a tell. Whether or not it's deserved.

The pivot plan in `docs/launch-r-python.md` reframes the project as engineering-first (FastAPI + React + Three.js + 790 tests) rather than physics-first. r/Python skeptics ask "is the test suite real" instead of "is this crank physics", which is a fight I can win because the answer is "yes, here's what's in it".

---

## Things I'd do differently if starting over

- Start with the test gates, not the code. The first thing in `tests/test_schwarzschild.py` should be the canonical Hawking-T value with a `pytest.approx(rel=1e-15)` check. *Then* write the class. I did the inverse and had to retrofit half the tests.
- Don't put Pydantic models in the same file as the physics class. They cross-import in annoying ways. Put the API schemas in `backend/app/schemas/`, leave the physics modules as pure scientific Python with no FastAPI awareness.
- Pick a unit system on day 1 and document it. I have geometric (G=c=1) and "physical" (SI-ish, with a `physical_units=True` flag). The conversions live in three places. Should be in one.
- Render free tier is fine for a launch but the cold-start kills the hostile-reader narrative ("see, the demo doesn't even load"). Either pre-warm aggressively before traffic events or budget $7/mo for Starter.

---

## Open questions I haven't resolved

- Is the de Sitter Gibbons-Hawking entropy `S = π L²` *really* the entropy of a horizon you don't own? The math checks out; the interpretation feels weirder the more I think about it.
- The Cardy → Bekenstein-Hawking match for BTZ is bit-exact. Why the universe is so kind as to make this work is way above my pay grade. Asking around.
- Page curve for evaporating Schwarzschild: my toy model returns to zero at `t_evap`. Real semi-classical calculations probably don't. How wrong is the toy?

If you have answers, open an issue.
