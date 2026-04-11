r"""Time-domain ringdown waveform generator.

A perturbed black hole settles to its final stationary state by
radiating its memory of the perturbation in a sum of damped
sinusoids — the *quasinormal modes*.  The strain at a distant
detector is

.. math::

    h(t) = \sum_{\ell m n} A_{\ell m n}\,
           \cos\!\big(\omega_R^{\ell m n}(t - t_0) + \phi_{\ell m n}\big)\,
           e^{-\omega_I^{\ell m n}(t - t_0)},

for :math:`t > t_0`, where :math:`\omega = \omega_R - i \omega_I`
is the QNM complex frequency in the convention used by
:mod:`spacetime_lab.waves.qnm`.

The amplitudes :math:`A_{\ell m n}` and phases
:math:`\phi_{\ell m n}` depend on the formation history of the
remnant (the merger that produced it).  In Phase 5 we treat them
as user inputs; a future phase could compute them from initial
data via Green's functions or matched-filter fits.

The frequencies and damping rates depend **only on the BH mass
and spin**.  This is the cleanest separation in all of GW
astronomy: the ringdown spectrum is the universal "ringtone" of a
remnant Kerr BH and is the basis for the no-hair theorem test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RingdownMode:
    r"""A single damped sinusoid contributing to the ringdown.

    Parameters
    ----------
    omega : complex
        QNM complex frequency :math:`\omega_R - i\omega_I` in units
        of the BH mass :math:`M` (i.e. the same units as
        :class:`QNMResult.omega`).
    amplitude : float
        Dimensionless amplitude :math:`A` of this mode.
    phase : float
        Initial phase :math:`\phi` (radians) of this mode.
    """

    omega: complex
    amplitude: float
    phase: float = 0.0


class RingdownWaveform:
    r"""Time-domain ringdown waveform from a list of QNMs.

    Parameters
    ----------
    mass : float
        Final remnant BH mass in geometric units (:math:`G = c = 1`).
        Used to convert the dimensionless ``omega`` of each
        :class:`RingdownMode` into a physical frequency.  Set
        ``mass = 1.0`` to keep everything dimensionless.
    modes : list of RingdownMode
        The QNMs to superpose.  Most of the time the dominant mode
        :math:`(\ell, m, n) = (2, m, 0)` is enough; including the
        first overtone :math:`(2, m, 1)` gives a noticeably better
        match to the early ringdown.

    Examples
    --------
    The dominant Schwarzschild gravitational mode of a remnant
    with mass :math:`M = 1`::

        >>> from spacetime_lab.waves import (
        ...     leaver_qnm_schwarzschild, RingdownMode, RingdownWaveform,
        ... )
        >>> qnm = leaver_qnm_schwarzschild(l=2, n=0)
        >>> rd = RingdownWaveform(
        ...     mass=1.0,
        ...     modes=[RingdownMode(omega=qnm.omega, amplitude=1.0)],
        ... )
        >>> import numpy as np
        >>> t = np.linspace(0, 100, 1000)
        >>> h = rd.evaluate(t)
    """

    def __init__(self, mass: float, modes: list[RingdownMode]) -> None:
        if mass <= 0:
            raise ValueError(f"mass must be positive, got {mass}")
        if len(modes) == 0:
            raise ValueError("must supply at least one RingdownMode")
        self.mass = float(mass)
        self.modes: list[RingdownMode] = list(modes)

    def evaluate(self, t: np.ndarray, t_start: float = 0.0) -> np.ndarray:
        r"""Evaluate the ringdown strain at given times.

        Parameters
        ----------
        t : array_like
            Times at which to evaluate, in the same geometric units
            as ``mass``.  Values with ``t < t_start`` give zero.
        t_start : float
            Start time :math:`t_0` of the ringdown.  Default 0.

        Returns
        -------
        numpy.ndarray
            The strain :math:`h(t)`, dimensionless.
        """
        t = np.asarray(t, dtype=float)
        h = np.zeros_like(t)
        # Build the signal only for t >= t_start.  Earlier times are 0.
        active = t >= t_start
        dt = t[active] - t_start
        for mode in self.modes:
            # omega is in M=1 units, so the physical angular
            # frequency is omega / M.
            omega_R_phys = mode.omega.real / self.mass
            omega_I_phys = (-mode.omega.imag) / self.mass  # damping rate
            envelope = mode.amplitude * np.exp(-omega_I_phys * dt)
            oscillation = np.cos(omega_R_phys * dt + mode.phase)
            h[active] += envelope * oscillation
        return h

    def fundamental_period(self) -> float:
        """Period of the most slowly oscillating mode, in geometric units.

        Useful for choosing a sensible time array.
        """
        slowest = min(self.modes, key=lambda m: abs(m.omega.real))
        return 2.0 * np.pi * self.mass / abs(slowest.omega.real)

    def longest_damping_time(self) -> float:
        """Damping time of the least-damped mode, in geometric units.

        Useful for choosing a sensible time-array length.
        """
        least_damped = min(self.modes, key=lambda m: abs(m.omega.imag))
        return self.mass / abs(least_damped.omega.imag)
