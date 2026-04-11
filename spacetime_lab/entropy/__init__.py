"""Quantum information primitives for entanglement entropy and beyond.

Phase 6 of the Spacetime Lab roadmap.  Provides the building blocks
needed to compute entanglement entropies of pure and mixed quantum
states, plus the Schmidt decomposition that underlies every
tensor-network method we will use in Phases 7-9.

The motivation is **holography**: in Phase 7+ we will compute the
holographic entanglement entropy of a CFT subregion via the
Ryu-Takayanagi formula

.. math::

    S_A^{\\text{boundary}} = \\frac{\\text{Area}(\\gamma_A^{\\text{bulk}})}{4 G_N},

where :math:`\\gamma_A` is a minimal surface in the bulk anchored to
the boundary of :math:`A`.  The right-hand side is geometric (Phase
1, 3, 4 territory); the left-hand side is the von Neumann entropy of
a reduced density matrix on the boundary CFT — and that is what this
module computes.

What this module provides
=========================

- :func:`density_matrix(state)` — promote a pure-state vector to its
  density-matrix form :math:`\\rho = |\\psi\\rangle\\langle\\psi|`.
- :func:`partial_trace(rho, dims, traced)` — compute the reduced
  density matrix on the complement of ``traced`` for a state on a
  composite Hilbert space :math:`\\mathcal{H}_0 \\otimes \\cdots \\otimes
  \\mathcal{H}_{n-1}` with dimensions ``dims``.
- :func:`is_pure(rho)`, :func:`is_density_matrix(rho)` — predicates.
- :func:`von_neumann_entropy(rho, base)` — the canonical
  :math:`S(\\rho) = -\\text{tr}(\\rho \\log \\rho)`.
- :func:`mutual_information(rho_AB, dims, A, B)` — the standard QI
  quantity :math:`I(A:B) = S(\\rho_A) + S(\\rho_B) - S(\\rho_{AB})`.
- :func:`schmidt_decomposition(state, dims)` — pull out Schmidt
  coefficients and Schmidt vectors via SVD on the reshaped state.
- :func:`schmidt_rank(state, dims)` — number of non-zero Schmidt
  coefficients.
- :func:`entanglement_entropy(state, dims, base)` — von Neumann
  entropy of the reduced density matrix on the first half of a
  bipartition.  Convenience wrapper that uses the SVD form.

Verified against canonical analytic values
==========================================

- Bell pair :math:`(|00\\rangle + |11\\rangle)/\\sqrt{2}`:
  entanglement entropy = :math:`\\log 2` (1 bit).
- 3-qubit GHZ state: every 1-vs-2 bipartition has entropy
  :math:`\\log 2`.
- Maximally mixed state :math:`I_d / d`: entropy = :math:`\\log d`.
- Product state :math:`|\\phi\\rangle \\otimes |\\chi\\rangle`:
  entropy = 0.
- Additivity: :math:`S(\\rho_A \\otimes \\rho_B) = S(\\rho_A) + S(\\rho_B)`.

References
==========
- Nielsen & Chuang, *Quantum Computation and Quantum Information*,
  ch. 2 (Schmidt decomposition) and ch. 11 (entropy).
- Wikipedia, *Entropy of entanglement* and *Von Neumann entropy*.
- Calabrese & Cardy, *Entanglement entropy and quantum field
  theory*, J. Stat. Mech. 0406:P06002 (2004) — area law for QFT.
"""

from spacetime_lab.entropy.density import (
    density_matrix,
    is_density_matrix,
    is_pure,
    partial_trace,
)
from spacetime_lab.entropy.schmidt import (
    entanglement_entropy,
    schmidt_decomposition,
    schmidt_rank,
)
from spacetime_lab.entropy.von_neumann import (
    mutual_information,
    von_neumann_entropy,
)

__all__ = [
    "density_matrix",
    "entanglement_entropy",
    "is_density_matrix",
    "is_pure",
    "mutual_information",
    "partial_trace",
    "schmidt_decomposition",
    "schmidt_rank",
    "von_neumann_entropy",
]
