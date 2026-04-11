r"""Density matrices, partial traces, and related predicates.

A density matrix :math:`\rho` is a positive semidefinite, Hermitian
operator with unit trace.  Pure states correspond to rank-1 density
matrices :math:`\rho = |\psi\rangle\langle\psi|`; mixed states have
higher rank.

For a composite system on :math:`\mathcal{H}_0 \otimes \mathcal{H}_1
\otimes \cdots \otimes \mathcal{H}_{n-1}` with subsystem dimensions
:math:`(d_0, d_1, \ldots, d_{n-1})`, the **partial trace** over a
subset :math:`T` of the subsystems gives the reduced density matrix
on the complement :math:`\bar T`:

.. math::

    \rho_{\bar T} = \mathrm{tr}_T(\rho).

This module provides :func:`partial_trace` for arbitrary subsystem
dimensions and arbitrary traced-subsystem sets, plus the predicates
:func:`is_pure` and :func:`is_density_matrix`.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


# ─────────────────────────────────────────────────────────────────────
# Constructors
# ─────────────────────────────────────────────────────────────────────


def density_matrix(state: np.ndarray) -> np.ndarray:
    r"""Promote a pure-state vector to its density-matrix form.

    Returns :math:`\rho = |\psi\rangle\langle\psi|` for a normalised
    state vector :math:`|\psi\rangle`.

    Parameters
    ----------
    state : array_like
        A complex (or real) 1D array of length :math:`d`.  Need not
        be normalised — the function normalises it before forming
        the outer product.

    Returns
    -------
    numpy.ndarray
        A :math:`d \times d` complex Hermitian rank-1 matrix with
        trace 1.

    Examples
    --------
    >>> import numpy as np
    >>> psi = np.array([1.0, 0.0, 0.0, 0.0])  # |00> on 2 qubits
    >>> rho = density_matrix(psi)
    >>> rho.shape
    (4, 4)
    >>> float(np.trace(rho).real)
    1.0
    """
    state = np.asarray(state, dtype=complex).reshape(-1)
    norm = np.linalg.norm(state)
    if norm == 0:
        raise ValueError("state vector has zero norm")
    state = state / norm
    return np.outer(state, state.conj())


# ─────────────────────────────────────────────────────────────────────
# Predicates
# ─────────────────────────────────────────────────────────────────────


def is_density_matrix(rho: np.ndarray, atol: float = 1e-10) -> bool:
    r"""Test whether ``rho`` is a valid density matrix.

    Checks that :math:`\rho` is square, Hermitian, has trace 1, and
    is positive semidefinite (all eigenvalues :math:`\ge -atol`).

    Parameters
    ----------
    rho : array_like
        Candidate density matrix.
    atol : float
        Absolute tolerance for the trace, Hermiticity, and PSD checks.

    Returns
    -------
    bool
    """
    rho = np.asarray(rho)
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        return False
    if not np.allclose(rho, rho.conj().T, atol=atol):
        return False
    if not np.isclose(np.trace(rho).real, 1.0, atol=atol):
        return False
    if abs(np.trace(rho).imag) > atol:
        return False
    eigvals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    return bool(np.all(eigvals >= -atol))


def is_pure(rho: np.ndarray, atol: float = 1e-10) -> bool:
    r"""Test whether a density matrix represents a pure state.

    Pure states satisfy :math:`\mathrm{tr}(\rho^2) = 1`; mixed states
    have :math:`\mathrm{tr}(\rho^2) < 1`.

    Parameters
    ----------
    rho : array_like
    atol : float
        Tolerance for the comparison ``tr(rho^2) ≈ 1``.

    Returns
    -------
    bool
    """
    rho = np.asarray(rho)
    purity = np.trace(rho @ rho).real
    return bool(abs(purity - 1.0) < atol)


# ─────────────────────────────────────────────────────────────────────
# Partial trace
# ─────────────────────────────────────────────────────────────────────


def partial_trace(
    rho: np.ndarray,
    dims: Iterable[int],
    traced_subsystems: Iterable[int],
) -> np.ndarray:
    r"""Compute the partial trace over a subset of subsystems.

    For a density matrix :math:`\rho` on
    :math:`\mathcal{H}_0 \otimes \mathcal{H}_1 \otimes \cdots \otimes
    \mathcal{H}_{n-1}` with subsystem dimensions :math:`(d_0, \ldots,
    d_{n-1})`, return the reduced density matrix on the *complement*
    of the traced subsystems::

        rho_kept = tr_{traced} (rho).

    Parameters
    ----------
    rho : array_like
        A square density matrix of size :math:`(\prod_i d_i, \prod_i d_i)`.
    dims : tuple of int
        The subsystem dimensions, in order.  Must satisfy
        ``prod(dims) == rho.shape[0]``.
    traced_subsystems : tuple of int
        Indices of the subsystems to trace out, in the same numbering
        scheme as ``dims``.  Must be a subset of ``range(len(dims))``.

    Returns
    -------
    numpy.ndarray
        The reduced density matrix on the kept subsystems.  Its size
        is :math:`(\prod_{i \notin \text{traced}} d_i, \cdot)`.

    Notes
    -----
    Implementation: reshape :math:`\rho` from a 2-index matrix into a
    :math:`2n`-index tensor with shape ``(d_0, ..., d_{n-1}, d_0, ..., d_{n-1})``,
    contract pairs of indices corresponding to the traced subsystems
    via :func:`numpy.einsum`, then reshape back.

    Examples
    --------
    Bell pair, traced over qubit 1::

        >>> import numpy as np
        >>> from spacetime_lab.entropy import density_matrix, partial_trace
        >>> psi = np.array([1, 0, 0, 1]) / np.sqrt(2)
        >>> rho = density_matrix(psi)
        >>> rho_A = partial_trace(rho, dims=(2, 2), traced_subsystems=(1,))
        >>> rho_A
        array([[0.5+0.j, 0. +0.j],
               [0. +0.j, 0.5+0.j]])
    """
    rho = np.asarray(rho)
    dims = tuple(int(d) for d in dims)
    traced = tuple(int(t) for t in traced_subsystems)

    n = len(dims)
    total_dim = 1
    for d in dims:
        total_dim *= d
    if rho.shape != (total_dim, total_dim):
        raise ValueError(
            f"rho shape {rho.shape} does not match prod(dims) = {total_dim}"
        )
    if any(t < 0 or t >= n for t in traced):
        raise ValueError(
            f"traced_subsystems {traced} contains indices outside [0, {n})"
        )
    if len(set(traced)) != len(traced):
        raise ValueError(f"traced_subsystems {traced} contains duplicates")

    kept = [i for i in range(n) if i not in traced]

    # Reshape rho into a 2n-index tensor.  The first n indices are
    # the row multi-index, the last n are the column multi-index.
    tensor = rho.reshape(dims + dims)

    # Build einsum index labels.  We give each subsystem a unique
    # letter for its row index and another letter for its column index;
    # for traced subsystems we use the same letter for both, which
    # implements the trace.
    if 2 * n > 26:
        raise ValueError(
            f"partial_trace supports at most 13 subsystems, got {n}"
        )
    row_labels = [chr(ord("a") + i) for i in range(n)]
    col_labels = [chr(ord("a") + n + i) for i in range(n)]
    for t in traced:
        col_labels[t] = row_labels[t]

    in_labels = "".join(row_labels) + "".join(col_labels)
    out_row_labels = "".join(row_labels[i] for i in kept)
    out_col_labels = "".join(col_labels[i] for i in kept)
    out_labels = out_row_labels + out_col_labels

    contracted = np.einsum(f"{in_labels}->{out_labels}", tensor)

    kept_dim = 1
    for i in kept:
        kept_dim *= dims[i]
    return contracted.reshape(kept_dim, kept_dim)
