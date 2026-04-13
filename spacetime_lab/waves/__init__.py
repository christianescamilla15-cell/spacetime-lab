"""Gravitational waves from black holes.

Phase 5 of the Spacetime Lab roadmap, extended in the v1.2 patch
with Kerr QNMs.  Provides:

- :func:`leaver_qnm_schwarzschild` — Schwarzschild quasinormal mode
  finder via Leaver's 1985 continued-fraction method.  Verified
  against the canonical reference values from
  Berti, Cardoso & Starinets, *Class. Quantum Grav.* **26** 163001
  (2009), Table 1.
- :func:`kerr_qnm` (**v1.2**) — Kerr QNM front-end at dimensionless
  spin :math:`a/M \\in [0, 1)`.  Breaks the Schwarzschild
  :math:`m`-degeneracy into :math:`2l + 1` distinct frequencies;
  prograde modes (:math:`m > 0`) are less damped than retrograde
  (:math:`m < 0`) at non-zero spin.
- :class:`QNMResult` dataclass holding the complex frequency and
  metadata for a single mode.  Kerr fields (``m``, ``a_over_M``)
  are populated only for Kerr modes.
- :class:`RingdownWaveform` — generator for the time-domain ringdown
  signal as a superposition of damped sinusoids, the universal
  late-time response of a perturbed BH.

The Schwarzschild QNM spectrum is the canonical 'ringtone' of a
non-rotating black hole: the dominant gravitational mode is
:math:`(\\ell, m, n) = (2, m, 0)` with

.. math::

    M\\omega \\approx 0.37367 - 0.08896\\,i,

independent of :math:`m` (the BH is spherically symmetric).  For a
Kerr BH the spectrum splits: :math:`M\\omega_{l=m=2, n=0}(a=0.98)
\\approx 0.864 - 0.076\\,i`, far from the Schwarzschild value, and
:math:`M\\omega_{l=2, m=-2, n=0}(a=0.98)` goes the other way.

BH spectroscopy — measuring two or more QNMs independently from
LIGO/Virgo ringdown data — is a test of the no-hair theorem: every
mode must be consistent with a single :math:`(M, a)` pair.
"""

from spacetime_lab.waves.qnm import (
    QNMResult,
    kerr_qnm,
    leaver_qnm_schwarzschild,
)
from spacetime_lab.waves.ringdown import (
    RingdownMode,
    RingdownWaveform,
)

__all__ = [
    "QNMResult",
    "RingdownMode",
    "RingdownWaveform",
    "kerr_qnm",
    "leaver_qnm_schwarzschild",
]
