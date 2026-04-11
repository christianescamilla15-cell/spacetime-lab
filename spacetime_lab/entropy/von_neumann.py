r"""Von Neumann entropy and mutual information.

The von Neumann entropy of a density matrix :math:`\rho` is

.. math::

    S(\rho) = -\mathrm{tr}(\rho \log \rho) = -\sum_i \lambda_i \log \lambda_i,

where :math:`\{\lambda_i\}` are the eigenvalues of :math:`\rho`.  The
convention :math:`0 \log 0 = 0` is enforced numerically.  The base of
the logarithm is selectable: ``"e"`` (nats, the physics default),
``"2"`` (bits, the QI default), or ``"10"``.

Bounds:

- :math:`S(\rho) \ge 0`, with equality iff :math:`\rho` is pure.
- :math:`S(\rho) \le \log d`, with equality iff :math:`\rho = I/d`
  (the maximally mixed state on a :math:`d`-dimensional Hilbert space).

The von Neumann entropy is unitarily invariant:
:math:`S(U \rho U^\dagger) = S(\rho)`.

For composite systems, the **mutual information** between two
subsystems :math:`A` and :math:`B` is

.. math::

    I(A : B) = S(\rho_A) + S(\rho_B) - S(\rho_{AB}),

which is non-negative for any joint state and zero iff the state is a
product :math:`\rho_{AB} = \rho_A \otimes \rho_B`.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


_LOG_BASES = {
    "e": np.log,
    "2": np.log2,
    "10": np.log10,
}


def _logarithm(base: str):
    """Return the logarithm function for the requested base."""
    if base not in _LOG_BASES:
        raise ValueError(
            f"base must be one of {sorted(_LOG_BASES)}, got {base!r}"
        )
    return _LOG_BASES[base]


def von_neumann_entropy(
    rho: np.ndarray,
    base: str = "e",
    eigenvalue_cutoff: float = 1e-15,
) -> float:
    r"""Compute the von Neumann entropy of a density matrix.

    .. math::

        S(\rho) = -\mathrm{tr}(\rho \log \rho)
                = -\sum_i \lambda_i \log \lambda_i.

    Parameters
    ----------
    rho : array_like
        A density matrix (Hermitian, positive semidefinite, unit
        trace).  We Hermitise it numerically before diagonalising.
    base : {"e", "2", "10"}
        Base of the logarithm.  Default ``"e"`` (entropy in nats).
        Use ``"2"`` for entropy in bits.
    eigenvalue_cutoff : float
        Eigenvalues with magnitude below this threshold are dropped
        from the sum, implementing the convention
        :math:`0 \log 0 = 0` numerically.  Also serves to suppress
        small negative eigenvalues from finite-precision artefacts.

    Returns
    -------
    float
        The von Neumann entropy.

    Examples
    --------
    Maximally mixed single qubit::

        >>> import numpy as np
        >>> rho = 0.5 * np.eye(2)
        >>> abs(von_neumann_entropy(rho) - np.log(2)) < 1e-12
        True

    Pure state has zero entropy::

        >>> psi = np.array([1.0, 0.0])
        >>> from spacetime_lab.entropy import density_matrix
        >>> rho = density_matrix(psi)
        >>> abs(von_neumann_entropy(rho)) < 1e-12
        True
    """
    log = _logarithm(base)
    rho = np.asarray(rho)
    # Hermitise to suppress floating-point asymmetries.
    rho_h = (rho + rho.conj().T) / 2
    eigvals = np.linalg.eigvalsh(rho_h)
    # Clip tiny negative values from finite-precision artefacts and
    # tiny positive values that would underflow the log.
    valid = eigvals > eigenvalue_cutoff
    if not np.any(valid):
        return 0.0
    return float(-np.sum(eigvals[valid] * log(eigvals[valid])))


def mutual_information(
    rho_AB: np.ndarray,
    dims: Iterable[int],
    subsystem_A: Iterable[int],
    subsystem_B: Iterable[int],
    base: str = "e",
) -> float:
    r"""Compute the quantum mutual information :math:`I(A : B)`.

    .. math::

        I(A : B) = S(\rho_A) + S(\rho_B) - S(\rho_{AB}).

    Parameters
    ----------
    rho_AB : array_like
        Joint density matrix on the union :math:`A \cup B \cup C`,
        where :math:`C` is whatever is not in :math:`A` or :math:`B`.
    dims : tuple of int
        Subsystem dimensions, in order.
    subsystem_A : tuple of int
        Indices of the subsystems comprising region :math:`A`.
    subsystem_B : tuple of int
        Indices of the subsystems comprising region :math:`B`.
        Must be disjoint from ``subsystem_A``.
    base : {"e", "2", "10"}
        Logarithm base.  Default ``"e"``.

    Returns
    -------
    float
        :math:`I(A : B) \ge 0`, with equality iff
        :math:`\rho_{AB} = \rho_A \otimes \rho_B` *as a state on
        the union*.

    Notes
    -----
    The "joint" :math:`\rho_{AB}` here is the reduced density matrix
    on :math:`A \cup B`, obtained by tracing out everything else.
    For a global state :math:`\rho` on the full system, you should
    pass ``partial_trace(rho, dims, traced=C)`` as ``rho_AB``.
    """
    from spacetime_lab.entropy.density import partial_trace

    dims = tuple(int(d) for d in dims)
    A = tuple(int(a) for a in subsystem_A)
    B = tuple(int(b) for b in subsystem_B)
    if set(A) & set(B):
        raise ValueError(
            f"subsystem_A {A} and subsystem_B {B} must be disjoint"
        )

    n = len(dims)
    all_subs = set(range(n))
    rho_A = partial_trace(rho_AB, dims, traced_subsystems=tuple(all_subs - set(A)))
    rho_B = partial_trace(rho_AB, dims, traced_subsystems=tuple(all_subs - set(B)))
    rho_AB_only = partial_trace(
        rho_AB, dims, traced_subsystems=tuple(all_subs - set(A) - set(B))
    )

    return (
        von_neumann_entropy(rho_A, base=base)
        + von_neumann_entropy(rho_B, base=base)
        - von_neumann_entropy(rho_AB_only, base=base)
    )
