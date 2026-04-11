r"""Schwarzschild quasinormal modes via the canonical reference solver.

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
- :class:`QNMResult` — small dataclass holding the complex frequency
  and metadata.

Both are thin wrappers over
:class:`qnm.schwarzschild.overtonesequence.SchwOvertoneSeq`, with
the same sign / time-convention as Berti, Cardoso & Starinets,
*Class. Quantum Grav.* **26** 163001 (2009).

What this module does **not** provide
=====================================

- A from-scratch implementation of the Leaver coefficients.  See
  the design notes in v0.5.0 for the rationale.  The coefficients
  are subtle (3 different sign / spin-weight conventions float
  around the literature), our first attempt to write them from
  memory failed verification at the canonical Berti et al value
  ``M*omega = 0.37367 - 0.08896 i``, and rather than blindly tuning
  signs we delegate to a reference implementation that is already
  verified against published tables to ~1e-16.
- Kerr QNMs.  ``qnm`` provides them but Spacetime Lab v0.5.0 only
  exposes the Schwarzschild front-end; the Kerr wrapper will land
  in a future patch.

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
    r"""A single Schwarzschild quasinormal mode.

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
        mode is :math:`M\omega \approx 0.37367 - 0.08896\,i`, with
        the *negative* imaginary part indicating exponential decay
        under the :math:`e^{-i\omega t}` Fourier convention.
    cf_truncation_error : float
        Estimated truncation error of the continued fraction at the
        depth used.  ~1e-16 (machine precision) for the lowest few
        modes.
    n_cf_terms : int
        Number of continued-fraction terms used to converge to the
        reported precision.
    """

    l: int
    n: int
    s: int
    omega: complex
    cf_truncation_error: float
    n_cf_terms: int


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
