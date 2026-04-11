"""Gravitational waves from black holes.

Phase 5 of the Spacetime Lab roadmap.  Provides:

- :func:`leaver_qnm_schwarzschild` — Schwarzschild quasinormal mode
  finder via Leaver's 1985 continued-fraction method.  Verified
  against the canonical reference values from
  Berti, Cardoso & Starinets, *Class. Quantum Grav.* **26** 163001
  (2009), Table 1.
- :class:`QNMResult` dataclass holding the complex frequency and
  metadata for a single mode.
- :class:`RingdownWaveform` — generator for the time-domain ringdown
  signal as a superposition of damped sinusoids, the universal late
  time response of a perturbed BH.

The Schwarzschild QNM spectrum is the canonical 'ringtone' of a
non-rotating black hole: the dominant gravitational mode is
:math:`(\\ell, m, n) = (2, m, 0)` with

.. math::

    M\\omega \\approx 0.37367 - 0.08896\\,i.

Higher overtones :math:`n = 1, 2, \\ldots` are increasingly damped
and rarely observed in practice.  Higher multipoles
:math:`\\ell = 3, 4, \\ldots` are sub-dominant and only become
important for systems with significant asymmetry.

Kerr QNMs are not yet implemented; they require simultaneous
solution of an angular spheroidal-harmonic eigenvalue problem and
a 5-term radial recurrence, both of which are beyond the v0.5.0
scope.  Schwarzschild QNMs are the right starting point: they
verify the entire numerical pipeline against published values to
better than 1 part in 10^6, and the resulting ringdown waveforms
are qualitatively the same as what LIGO sees.
"""

from spacetime_lab.waves.qnm import (
    QNMResult,
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
    "leaver_qnm_schwarzschild",
]
