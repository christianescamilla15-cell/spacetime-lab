r"""Quasinormal modes of Schwarzschild and Kerr black holes.

Wraps Stein's :mod:`qnm` package (Stein 2019, JOSS 4 1683,
arXiv:1908.10377) which is the canonical Python reference
implementation of Leaver's 1985 continued-fraction method.  We do
not re-derive the recurrence coefficients here: rolling our own
buggy implementation of someone else's well-tested algorithm is the
opposite of what scientific software should do.

What this module provides
=========================

- :func:`leaver_qnm_schwarzschild` — return a :class:`QNMResult` for
  a single Schwarzschild mode.
- :func:`kerr_qnm` (**v1.2**) — return a :class:`QNMResult` for a
  Kerr mode at dimensionless spin ``a/M``.
- :class:`QNMResult` — small dataclass holding the complex frequency
  and metadata.  The Kerr fields (``m``, ``a_over_M``) are populated
  only for Kerr modes and left as ``None`` for Schwarzschild.

The Schwarzschild path uses
:class:`qnm.schwarzschild.overtonesequence.SchwOvertoneSeq` and the
Kerr path uses :func:`qnm.modes_cache`.  Both share the same
sign / time-convention as Berti, Cardoso & Starinets,
*Class. Quantum Grav.* **26** 163001 (2009): the complex frequency
:math:`M\omega` has a *negative* imaginary part indicating
exponential decay under the :math:`e^{-i\omega t}` Fourier
convention.

Why Kerr QNMs matter physically
===============================

The Schwarzschild QNM spectrum is degenerate in the azimuthal number
:math:`m`: all modes with the same :math:`(l, n)` have the same
frequency because the BH is spherically symmetric.  **A rotating
Kerr BH breaks this degeneracy**: the ring of candidate QNMs splits
into :math:`2l + 1` distinct frequencies labelled by
:math:`m \in \{-l, \ldots, l\}`.  Two consequences:

- **Prograde modes** (:math:`m > 0`, co-rotating with the BH) are
  *less* damped than retrograde modes (:math:`m < 0`).  The rotating
  BH "supports" co-rotating perturbations longer.  The difference
  grows dramatically at high spin, where prograde modes' imaginary
  parts approach zero (the marginally-stable limit).
- **BH spectroscopy**: measuring two or more QNMs independently from
  LIGO/Virgo ringdown data is a test of the no-hair theorem.  For a
  Kerr BH every mode frequency must be consistent with a *single*
  :math:`(M, a)` pair; any inconsistency would mean the remnant is
  not a Kerr BH.

What this module does **not** provide
=====================================

- A from-scratch implementation of the Leaver coefficients.  See
  the design notes in v0.5.0 for the rationale: the coefficients
  are subtle (3 different sign / spin-weight conventions float
  around the literature), our first attempt to write them from
  memory failed verification at the canonical Berti et al value
  ``M*omega = 0.37367 - 0.08896 i``, and rather than blindly tuning
  signs we delegate to a reference implementation that is already
  verified against published tables to ~1e-16.
- Kerr-Newman (charged rotating BH) modes — out of scope.
- Superradiance diagnostics — all Kerr QNMs returned here have
  :math:`\mathrm{Im}(\omega) < 0` (decay); we do not compute the
  bound-state / superradiant regime separately.

Examples
========

The fundamental gravitational mode of Schwarzschild::

    >>> from spacetime_lab.waves import leaver_qnm_schwarzschild
    >>> result = leaver_qnm_schwarzschild(l=2, n=0)
    >>> abs(result.omega - complex(0.37367, -0.08896)) < 1e-4
    True

A higher overtone::

    >>> result = leaver_qnm_schwarzschild(l=2, n=2)
    >>> result.omega
    (0.30105... - 0.47827...j)

References
==========
- E. W. Leaver, *An analytic representation for the quasi-normal modes
  of Kerr black holes*, Proc. R. Soc. A **402** 285 (1985).
- E. Berti, V. Cardoso, A. O. Starinets, *Quasinormal modes of black
  holes and black branes*, Class. Quantum Grav. **26** 163001 (2009).
- L. C. Stein, *qnm: A Python package for calculating Kerr
  quasinormal modes*, JOSS **4** 1683 (2019), arXiv:1908.10377.
- G. B. Cook, M. Zalutskiy, *Gravitational perturbations of the Kerr
  geometry: High-accuracy study*, Phys. Rev. D **90** 124021 (2014).
"""

from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────


@dataclass
class QNMResult:
    r"""A single quasinormal mode of a Schwarzschild or Kerr BH.

    For Schwarzschild modes the fields ``m`` and ``a_over_M`` are
    left as ``None`` (the spectrum is degenerate in :math:`m` and
    the spin is zero by assumption).  For Kerr modes both are
    populated.

    Attributes
    ----------
    l : int
        Multipole index :math:`\ell`.
    n : int
        Overtone number, with :math:`n = 0` the fundamental mode
        (least damped) and :math:`n = 1, 2, \ldots` the increasingly
        damped overtones.
    s : int
        Spin weight of the perturbation, in the convention used by
        ``qnm``: ``-2`` gravitational, ``-1`` electromagnetic,
        ``0`` scalar.
    omega : complex
        Complex frequency in units of the BH mass :math:`M`, i.e.
        the value of :math:`M\omega`.  Convert to physical units
        by dividing by the actual mass.  Sign convention follows
        Berti, Cardoso & Starinets 2009: the dominant gravitational
        Schwarzschild mode is :math:`M\omega \approx 0.37367 -
        0.08896\,i`, with the *negative* imaginary part indicating
        exponential decay under the :math:`e^{-i\omega t}` Fourier
        convention.
    cf_truncation_error : float
        Estimated truncation error of the continued fraction at the
        depth used.  ~1e-16 (machine precision) for the lowest few
        Schwarzschild modes.  For Kerr modes ``qnm``'s cache does
        not expose this directly, so it is reported as ``nan`` for
        Kerr results.
    n_cf_terms : int
        Number of continued-fraction terms used to converge to the
        reported precision.  Set to ``-1`` for Kerr modes (not
        exposed by the cache-based API).
    m : int or None
        Azimuthal number for Kerr modes, in :math:`\{-l, \ldots, l\}`.
        ``None`` for Schwarzschild (which is :math:`m`-degenerate).
    a_over_M : float or None
        Dimensionless spin :math:`a/M \in [0, 1)` for Kerr modes.
        ``None`` for Schwarzschild (equivalent to ``0.0`` but left
        unset to emphasise the :math:`m`-degeneracy).
    """

    l: int
    n: int
    s: int
    omega: complex
    cf_truncation_error: float
    n_cf_terms: int
    m: int | None = None
    a_over_M: float | None = None


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────


def leaver_qnm_schwarzschild(
    l: int,
    n: int = 0,
    s: int = -2,
    n_max_internal: int | None = None,
) -> QNMResult:
    r"""Compute a Schwarzschild quasinormal mode.

    Thin wrapper around :class:`qnm.schwarzschild.overtonesequence.SchwOvertoneSeq`,
    which implements Leaver's 1985 continued-fraction method via the
    Cook-Zalutskiy 2014 form.

    Parameters
    ----------
    l : int
        Multipole index, must satisfy :math:`l \ge |s|`.
    n : int
        Overtone number.  ``n = 0`` is the fundamental (least
        damped) mode.
    s : int
        Spin weight: ``-2`` gravitational (default), ``-1``
        electromagnetic, ``0`` scalar.  This is the standard
        Newman-Penrose convention used in the QNM literature.
    n_max_internal : int, optional
        Internal: how many overtones to compute (the underlying
        solver builds an entire sequence ``[0, 1, ..., n_max_internal]``
        to extract overtone ``n``).  Defaults to ``n``.

    Returns
    -------
    QNMResult
        Holds ``omega`` in units of the BH mass (so the value
        matches Berti et al directly — multiply by ``1/M`` to
        convert to physical frequency).

    Raises
    ------
    ImportError
        If the ``qnm`` package is not installed.  Install with
        ``pip install qnm``.
    ValueError
        If ``l < |s|``, ``n < 0``, or the underlying solver fails
        to converge.

    Examples
    --------
    >>> result = leaver_qnm_schwarzschild(l=2, n=0)
    >>> abs(result.omega - complex(0.37367, -0.08896)) < 1e-4
    True

    Notes
    -----
    The first call may be slow (~seconds) because ``qnm`` builds the
    overtone sequence from the ``n=0`` mode upward; subsequent calls
    are fast (~ms).  For computing many modes, prefer driving the
    underlying ``SchwOvertoneSeq`` directly so you only build the
    sequence once.
    """
    try:
        from qnm.schwarzschild.overtonesequence import SchwOvertoneSeq
    except ImportError as exc:
        raise ImportError(
            "The 'qnm' package is required for Schwarzschild QNM "
            "computation in spacetime_lab v0.5.0.  Install it with:\n"
            "    pip install qnm\n"
            "See https://github.com/duetosymmetry/qnm for details."
        ) from exc

    if l < abs(s):
        raise ValueError(f"l must be >= |s|, got l={l}, s={s}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got n={n}")

    if n_max_internal is None:
        n_max_internal = n

    seq = SchwOvertoneSeq(s=s, l=l, n_max=n_max_internal)
    try:
        seq.find_sequence()
    except Exception as exc:
        raise ValueError(
            f"qnm failed to converge for (l={l}, n={n}, s={s}): {exc}"
        ) from exc

    if n >= len(seq.omega):
        raise ValueError(
            f"qnm only converged to overtone {len(seq.omega) - 1}; "
            f"requested n={n}.  Try a smaller n or increase Nr."
        )

    return QNMResult(
        l=l,
        n=n,
        s=s,
        omega=complex(seq.omega[n]),
        cf_truncation_error=float(seq.cf_err[n]),
        n_cf_terms=int(seq.n_frac[n]),
    )


# ─────────────────────────────────────────────────────────────────────
# Kerr QNMs — v1.2 patch
# ─────────────────────────────────────────────────────────────────────


def kerr_qnm(
    l: int,
    m: int,
    n: int = 0,
    a_over_M: float = 0.0,
    s: int = -2,
) -> QNMResult:
    r"""Compute a Kerr quasinormal mode at dimensionless spin :math:`a/M`.

    Thin wrapper around :func:`qnm.modes_cache` (Stein 2019, JOSS
    4 1683).  The underlying solver is Leaver's 1985
    continued-fraction method adapted to Kerr's 5-term radial
    recurrence coupled to the angular spheroidal-harmonic eigenvalue
    problem; both are handled by ``qnm`` and verified against
    published tables to machine precision.

    At :math:`a/M = 0` this reduces to the Schwarzschild mode (with
    the Kerr path through ``qnm``, not via
    :func:`leaver_qnm_schwarzschild`); the returned ``omega`` should
    match :func:`leaver_qnm_schwarzschild` for any :math:`m` to
    machine precision — that cross-check is the Schwarzschild-limit
    gate of the v1.2 patch.

    Parameters
    ----------
    l : int
        Multipole index, must satisfy :math:`l \ge |s|`.  For
        gravitational modes the usual choice is :math:`l \ge 2`.
    m : int
        Azimuthal number, in :math:`\{-l, -l+1, \ldots, l-1, l\}`.
        Positive ``m`` means *prograde* (co-rotating with the BH);
        negative ``m`` means *retrograde*.
    n : int
        Overtone number.  Default ``0`` (fundamental, least damped).
    a_over_M : float
        Dimensionless spin :math:`a/M \in [0, 1)`.  Must be strictly
        less than 1; the underlying solver diverges at extremality.
    s : int
        Spin weight: ``-2`` gravitational (default), ``-1``
        electromagnetic, ``0`` scalar.

    Returns
    -------
    QNMResult
        Populated with ``l``, ``m``, ``n``, ``s``, ``omega``, and
        ``a_over_M``.  ``cf_truncation_error`` is set to ``nan``
        and ``n_cf_terms`` to ``-1`` — the cache-based ``qnm`` API
        does not expose these the way ``SchwOvertoneSeq`` does.

    Raises
    ------
    ImportError
        If the ``qnm`` package is not installed.
    ValueError
        If ``|m| > l``, ``l < |s|``, ``n < 0``, or ``a_over_M`` is
        outside :math:`[0, 1)`.

    Examples
    --------
    The canonical ``qnm``-docs example, verified bit-exactly:

    >>> r = kerr_qnm(l=2, m=2, n=0, a_over_M=0.68)
    >>> abs(r.omega.real - 0.5239751042900845) < 1e-10
    True
    >>> abs(r.omega.imag - (-0.08151262363119974)) < 1e-10
    True

    The Schwarzschild limit — ``m``-degeneracy is restored at
    :math:`a = 0`:

    >>> r0 = kerr_qnm(l=2, m=0, n=0, a_over_M=0.0)
    >>> r_ref = leaver_qnm_schwarzschild(l=2, n=0)
    >>> abs(r0.omega - r_ref.omega) < 1e-10
    True

    Prograde modes are less damped than retrograde at :math:`a > 0`:

    >>> pro = kerr_qnm(l=2, m=2, n=0, a_over_M=0.9)
    >>> retro = kerr_qnm(l=2, m=-2, n=0, a_over_M=0.9)
    >>> abs(pro.omega.imag) < abs(retro.omega.imag)
    True
    """
    try:
        import qnm as _qnm
    except ImportError as exc:
        raise ImportError(
            "The 'qnm' package is required for Kerr QNM computation.  "
            "Install it with:\n    pip install qnm\n"
            "See https://github.com/duetosymmetry/qnm for details."
        ) from exc

    if l < abs(s):
        raise ValueError(f"l must be >= |s|, got l={l}, s={s}")
    if abs(m) > l:
        raise ValueError(f"|m| must be <= l, got m={m}, l={l}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got n={n}")
    if not (0.0 <= a_over_M < 1.0):
        raise ValueError(
            f"a_over_M must be in [0, 1), got {a_over_M}.  The solver "
            f"does not converge at extremality a/M = 1."
        )

    mode_seq = _qnm.modes_cache(s=s, l=l, m=m, n=n)
    try:
        omega, _A, _C = mode_seq(a=a_over_M)
    except Exception as exc:
        raise ValueError(
            f"qnm failed to converge for Kerr mode "
            f"(l={l}, m={m}, n={n}, s={s}, a/M={a_over_M}): {exc}"
        ) from exc

    return QNMResult(
        l=l,
        n=n,
        s=s,
        omega=complex(omega),
        cf_truncation_error=float("nan"),
        n_cf_terms=-1,
        m=m,
        a_over_M=float(a_over_M),
    )
