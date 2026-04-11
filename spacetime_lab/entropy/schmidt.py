r"""Schmidt decomposition and the entanglement entropy of a bipartition.

For a pure state :math:`|\psi\rangle \in \mathcal{H}_A \otimes
\mathcal{H}_B`, the Schmidt decomposition is

.. math::

    |\psi\rangle = \sum_{i=1}^{r} \lambda_i\, |u_i\rangle_A \otimes |v_i\rangle_B,

with orthonormal :math:`\{|u_i\rangle\}` and :math:`\{|v_i\rangle\}`
and Schmidt coefficients :math:`\lambda_i > 0` satisfying
:math:`\sum_i \lambda_i^2 = 1`.

Computationally, the Schmidt decomposition is the singular value
decomposition (SVD) of the state vector reshaped as a
:math:`d_A \times d_B` matrix:

.. math::

    C = U \Sigma V^\dagger,

so :math:`\lambda_i = \sigma_i` are the singular values, the columns
of :math:`U` are the :math:`|u_i\rangle_A`, and the conjugated rows of
:math:`V^\dagger` are the :math:`|v_i\rangle_B`.

The reduced density matrices on each side have eigenvalues
:math:`\lambda_i^2`, so the entanglement entropy of the bipartition is

.. math::

    S = -\sum_i \lambda_i^2 \log \lambda_i^2.

This module provides:

- :func:`schmidt_decomposition` — return the Schmidt coefficients
  and the two sets of Schmidt vectors.
- :func:`schmidt_rank` — number of non-zero Schmidt coefficients.
- :func:`entanglement_entropy` — convenience that goes
  state -> SVD -> entropy in one call, without ever building the
  reduced density matrix explicitly.
"""

from __future__ import annotations

import numpy as np

from spacetime_lab.entropy.von_neumann import _logarithm


def schmidt_decomposition(
    state: np.ndarray,
    dims: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r"""Return the Schmidt decomposition of a pure bipartite state.

    Parameters
    ----------
    state : array_like
        A complex 1D array of length :math:`d_A \cdot d_B`.  Will be
        normalised internally.
    dims : tuple of (int, int)
        ``(d_A, d_B)`` — the dimensions of the two subsystems.

    Returns
    -------
    schmidt_coeffs : numpy.ndarray
        1D array of length ``min(d_A, d_B)``, the Schmidt
        coefficients :math:`\lambda_i \ge 0`, sorted in decreasing
        order.  These satisfy :math:`\sum_i \lambda_i^2 = 1`.
    U_A : numpy.ndarray
        :math:`d_A \times \min(d_A, d_B)` matrix.  Columns are the
        Schmidt basis vectors :math:`|u_i\rangle_A`.
    V_B : numpy.ndarray
        :math:`d_B \times \min(d_A, d_B)` matrix.  Columns are the
        Schmidt basis vectors :math:`|v_i\rangle_B`.

    Notes
    -----
    Reconstructing the state::

        coeffs, U, V = schmidt_decomposition(psi, (dA, dB))
        psi_recon = sum(coeffs[i] * np.kron(U[:, i], V[:, i])
                        for i in range(len(coeffs)))
    """
    state = np.asarray(state, dtype=complex).reshape(-1)
    d_A, d_B = int(dims[0]), int(dims[1])
    if state.size != d_A * d_B:
        raise ValueError(
            f"state has {state.size} components but dims=({d_A},{d_B}) "
            f"requires {d_A * d_B}"
        )
    norm = np.linalg.norm(state)
    if norm == 0:
        raise ValueError("state vector has zero norm")
    state = state / norm

    # Reshape into a d_A x d_B matrix and SVD: C = U Sigma V^dag
    matrix = state.reshape(d_A, d_B)
    U, sigma, Vh = np.linalg.svd(matrix, full_matrices=False)
    # Schmidt vectors on side B: the i-th vector is the i-th row of
    # V^dagger, which means in column form it is the i-th column of
    # V^dagger transposed (i.e. (Vh.T)[:, i]).  We return that as a
    # matrix so the user can Kronecker U[:, i] with V[:, i] directly
    # to reconstruct |psi>.  Equivalently, V = Vh.T.
    V = Vh.T
    return sigma, U, V


def schmidt_rank(
    state: np.ndarray,
    dims: tuple[int, int],
    atol: float = 1e-12,
) -> int:
    r"""Return the Schmidt rank of a pure bipartite state.

    The Schmidt rank is the number of strictly non-zero Schmidt
    coefficients (above the tolerance ``atol``).  Equivalently, the
    rank of the reduced density matrix :math:`\rho_A`.

    A Schmidt rank of 1 means the state is a product state
    :math:`|\phi\rangle_A \otimes |\chi\rangle_B`; any larger value
    means non-trivial entanglement.

    Parameters
    ----------
    state : array_like
    dims : tuple of (int, int)
    atol : float
        Coefficients below this value are considered zero.

    Returns
    -------
    int
    """
    coeffs, _, _ = schmidt_decomposition(state, dims)
    return int(np.sum(coeffs > atol))


def entanglement_entropy(
    state: np.ndarray,
    dims: tuple[int, int],
    base: str = "e",
    eigenvalue_cutoff: float = 1e-15,
) -> float:
    r"""Entanglement entropy of a pure bipartite state.

    Computes :math:`S = -\sum_i \lambda_i^2 \log \lambda_i^2` from
    the Schmidt coefficients.  This is the von Neumann entropy of
    either reduced density matrix :math:`\rho_A = \rho_B` (which are
    isospectral on their nonzero eigenvalues), so it is symmetric in
    the two halves of the bipartition.

    Parameters
    ----------
    state : array_like
        Pure bipartite state vector.
    dims : tuple of (int, int)
        Dimensions of the two subsystems.
    base : {"e", "2", "10"}
        Logarithm base.  Default ``"e"`` (nats).
    eigenvalue_cutoff : float
        Squared coefficients below this threshold are dropped from
        the sum (the :math:`0 \log 0 = 0` convention).

    Returns
    -------
    float
        The entanglement entropy.

    Examples
    --------
    Bell pair has entanglement entropy :math:`\log 2`::

        >>> import numpy as np
        >>> bell = np.array([1, 0, 0, 1]) / np.sqrt(2)
        >>> abs(entanglement_entropy(bell, dims=(2, 2)) - np.log(2)) < 1e-12
        True

    Product state has zero entanglement::

        >>> product = np.kron([1, 0], [0, 1])  # |0> tensor |1>
        >>> abs(entanglement_entropy(product, dims=(2, 2))) < 1e-12
        True
    """
    log = _logarithm(base)
    coeffs, _, _ = schmidt_decomposition(state, dims)
    probs = coeffs ** 2
    valid = probs > eigenvalue_cutoff
    if not np.any(valid):
        return 0.0
    return float(-np.sum(probs[valid] * log(probs[valid])))
