"""Tests for the Phase 5 waves module.

QNM tests pin every value to the canonical Berti, Cardoso & Starinets
2009 review (CQG 26 163001), Table 1.  See the file header of
``spacetime_lab/waves/qnm.py`` for the verification trail.

The QNM finder is a thin wrapper over Stein's ``qnm`` package
(JOSS 4 1683, arXiv:1908.10377), which is the canonical Python
implementation of Leaver's 1985 continued-fraction method.  These
tests verify that the wrapper preserves the canonical sign /
unit conventions and exposes the right API surface.

The ringdown waveform tests are pure-Python and have no external
dependency beyond numpy.
"""

import math
import warnings

import numpy as np
import pytest

from spacetime_lab.waves import (
    QNMResult,
    RingdownMode,
    RingdownWaveform,
    leaver_qnm_schwarzschild,
)


# qnm package emits deprecation warnings from its pickled data files;
# silence them so test output is clean.
warnings.filterwarnings("ignore", category=Warning, module="qnm")


# ─────────────────────────────────────────────────────────────────────
# leaver_qnm_schwarzschild — verification against Berti et al 2009
# ─────────────────────────────────────────────────────────────────────


# Canonical Schwarzschild QNM frequencies M*omega from
# Berti, Cardoso & Starinets 2009, Table 1.  These are the values
# the test suite hard-asserts against.
BERTI_REFERENCE_VALUES = {
    (2, 0): complex(0.37367, -0.08896),
    (2, 1): complex(0.34671, -0.27391),
    (3, 0): complex(0.59944, -0.09270),
}


class TestQNMResult:
    """The QNMResult dataclass."""

    def test_construction(self):
        r = QNMResult(
            l=2, n=0, s=-2,
            omega=complex(0.37367, -0.08896),
            cf_truncation_error=1e-16,
            n_cf_terms=300,
        )
        assert r.l == 2
        assert r.n == 0
        assert r.s == -2
        assert r.omega.real > 0
        assert r.omega.imag < 0


class TestSchwarzschildQNMValidation:
    """Argument validation for the QNM finder."""

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            leaver_qnm_schwarzschild(l=2, n=-1)

    def test_l_below_spin_raises(self):
        """For gravitational s=-2 perturbations, l must be >= 2."""
        with pytest.raises(ValueError):
            leaver_qnm_schwarzschild(l=1, n=0, s=-2)

    def test_returns_qnm_result(self):
        result = leaver_qnm_schwarzschild(l=2, n=0)
        assert isinstance(result, QNMResult)
        assert result.l == 2
        assert result.n == 0
        assert result.s == -2


class TestSchwarzschildQNMReferenceValues:
    """Verify each Berti et al 2009 Table 1 value."""

    @pytest.mark.parametrize(
        "l,n,expected",
        [
            (2, 0, complex(0.37367, -0.08896)),
            (2, 1, complex(0.34671, -0.27391)),
            (3, 0, complex(0.59944, -0.09270)),
        ],
    )
    def test_matches_berti_table_1(self, l, n, expected):
        """Each computed M*omega must match Berti et al to ~5 decimals."""
        result = leaver_qnm_schwarzschild(l=l, n=n)
        # Berti et al table is published to 5 decimals, so 1e-4
        # is the right tolerance.
        assert abs(result.omega - expected) < 1e-4

    def test_machine_precision_internal(self):
        """The qnm package converges the CF to ~1e-16 internally."""
        result = leaver_qnm_schwarzschild(l=2, n=0)
        assert result.cf_truncation_error < 1e-12

    def test_negative_imaginary_part(self):
        """Sign convention: damped modes have Im omega < 0."""
        for l, n in BERTI_REFERENCE_VALUES:
            result = leaver_qnm_schwarzschild(l=l, n=n)
            assert result.omega.imag < 0, f"l={l} n={n}"

    def test_overtones_more_damped(self):
        """Higher overtones have larger |Im omega| (faster damping)."""
        n0 = leaver_qnm_schwarzschild(l=2, n=0)
        n1 = leaver_qnm_schwarzschild(l=2, n=1)
        assert abs(n1.omega.imag) > abs(n0.omega.imag)

    def test_higher_l_higher_real_freq(self):
        """Higher multipole has higher real-part oscillation frequency."""
        l2 = leaver_qnm_schwarzschild(l=2, n=0)
        l3 = leaver_qnm_schwarzschild(l=3, n=0)
        assert l3.omega.real > l2.omega.real


# ─────────────────────────────────────────────────────────────────────
# RingdownWaveform — pure-Python damped sinusoid generator
# ─────────────────────────────────────────────────────────────────────


class TestRingdownMode:
    def test_construction(self):
        m = RingdownMode(omega=complex(0.37, -0.09), amplitude=1.0)
        assert m.amplitude == 1.0
        assert m.phase == 0.0  # default
        assert m.omega.real == 0.37
        assert m.omega.imag == -0.09


class TestRingdownWaveformValidation:
    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            RingdownWaveform(
                mass=0.0,
                modes=[RingdownMode(omega=complex(0.37, -0.09), amplitude=1.0)],
            )

    def test_empty_modes_raises(self):
        with pytest.raises(ValueError):
            RingdownWaveform(mass=1.0, modes=[])


class TestRingdownWaveformEvaluation:
    def setup_method(self):
        self.qnm_omega = complex(0.37367, -0.08896)
        self.rd = RingdownWaveform(
            mass=1.0,
            modes=[RingdownMode(omega=self.qnm_omega, amplitude=1.0, phase=0.0)],
        )

    def test_initial_value(self):
        """At t=0 with phase=0 the strain should be the amplitude."""
        h = self.rd.evaluate(np.array([0.0]))
        assert math.isclose(h[0], 1.0)

    def test_zero_before_start_time(self):
        """Strain is zero for t < t_start."""
        t = np.array([-5.0, -1.0, 0.0, 1.0])
        h = self.rd.evaluate(t, t_start=0.0)
        assert h[0] == 0.0
        assert h[1] == 0.0
        assert h[2] != 0.0

    def test_oscillation_period(self):
        """Verify the strain returns to its initial value after one period."""
        T = 2.0 * math.pi / self.qnm_omega.real
        t = np.array([0.0, T])
        h = self.rd.evaluate(t)
        # After one period the cosine has cycled back, but the
        # exponential envelope has decayed by exp(-omega_I * T).
        decay = math.exp(self.qnm_omega.imag * T)
        assert math.isclose(h[1], h[0] * decay, rel_tol=1e-6)

    def test_envelope_decay(self):
        """At late times the strain envelope must follow exp(-omega_I * t)."""
        omega_I = -self.qnm_omega.imag  # damping rate, positive
        # Sample several periods later and look at the envelope
        period = 2.0 * math.pi / self.qnm_omega.real
        t = np.array([10 * period])
        h = self.rd.evaluate(t)
        expected_envelope = math.exp(-omega_I * 10 * period)
        # h(10T) = A * cos(0) * exp(-omega_I*10T) = expected_envelope
        assert math.isclose(h[0], expected_envelope, rel_tol=1e-6)

    def test_mass_scaling(self):
        """At a larger mass, the same QNM gives a slower oscillation."""
        rd2 = RingdownWaveform(
            mass=2.0,
            modes=[RingdownMode(omega=self.qnm_omega, amplitude=1.0)],
        )
        # Period should double when mass doubles
        T1 = 2 * math.pi * 1.0 / self.qnm_omega.real
        T2 = 2 * math.pi * 2.0 / self.qnm_omega.real
        assert math.isclose(self.rd.fundamental_period(), T1)
        assert math.isclose(rd2.fundamental_period(), T2)

    def test_multiple_modes_superpose_at_zero(self):
        """At t=0 with cos phases, h(0) = sum of amplitudes."""
        rd = RingdownWaveform(
            mass=1.0,
            modes=[
                RingdownMode(omega=complex(0.37, -0.09), amplitude=1.0, phase=0.0),
                RingdownMode(omega=complex(0.34, -0.27), amplitude=0.5, phase=0.0),
            ],
        )
        h = rd.evaluate(np.array([0.0]))
        assert math.isclose(h[0], 1.5)

    def test_phase_offset(self):
        """A pi/2 phase offset should give h(0) = A * cos(pi/2) = 0."""
        rd = RingdownWaveform(
            mass=1.0,
            modes=[
                RingdownMode(omega=complex(0.37, -0.09), amplitude=1.0, phase=math.pi / 2),
            ],
        )
        h = rd.evaluate(np.array([0.0]))
        assert math.isclose(h[0], 0.0, abs_tol=1e-12)


class TestRingdownDiagnostics:
    def test_fundamental_period(self):
        omega = complex(0.37367, -0.08896)
        rd = RingdownWaveform(
            mass=1.0,
            modes=[RingdownMode(omega=omega, amplitude=1.0)],
        )
        expected = 2 * math.pi / omega.real
        assert math.isclose(rd.fundamental_period(), expected)

    def test_longest_damping_time(self):
        omega = complex(0.37367, -0.08896)
        rd = RingdownWaveform(
            mass=1.0,
            modes=[RingdownMode(omega=omega, amplitude=1.0)],
        )
        expected = 1.0 / abs(omega.imag)
        assert math.isclose(rd.longest_damping_time(), expected)


# ─────────────────────────────────────────────────────────────────────
# End-to-end: QNM finder + ringdown waveform composition
# ─────────────────────────────────────────────────────────────────────


class TestQNMRingdownComposition:
    """Verify that the two halves of the waves module compose correctly."""

    def test_full_pipeline(self):
        """Compute the dominant Schwarzschild mode, build a waveform, eval."""
        qnm = leaver_qnm_schwarzschild(l=2, n=0)
        rd = RingdownWaveform(
            mass=1.0,
            modes=[RingdownMode(omega=qnm.omega, amplitude=1.0)],
        )
        t = np.linspace(0, 100, 500)
        h = rd.evaluate(t)
        assert h[0] == 1.0
        # Late-time amplitude should be small
        assert abs(h[-1]) < 1e-3

    def test_two_modes_pipeline(self):
        """Add the first overtone and check superposition."""
        n0 = leaver_qnm_schwarzschild(l=2, n=0)
        n1 = leaver_qnm_schwarzschild(l=2, n=1)
        rd = RingdownWaveform(
            mass=1.0,
            modes=[
                RingdownMode(omega=n0.omega, amplitude=1.0),
                RingdownMode(omega=n1.omega, amplitude=0.3),
            ],
        )
        h = rd.evaluate(np.array([0.0]))
        assert math.isclose(h[0], 1.3)
