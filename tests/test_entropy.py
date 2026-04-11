"""Tests for the Phase 6 entropy module.

Every assertion is pinned to a closed-form analytic value.  See the
file headers in ``spacetime_lab/entropy/`` for the verification
trail (Wikipedia, Nielsen & Chuang ch. 2 and 11).

The point of these tests is **operational sanity checks** rather
than rediscovery of physical constants:

- Bell pair entanglement = log 2 (1 bit) — the textbook canonical
  example.
- GHZ_3 every bipartition = log 2 — the canonical 3-qubit example.
- Maximally mixed state in dimension d has entropy log d.
- Pure states have entropy zero.
- Additivity for product states.
- Schmidt rank distinguishes product from entangled.
- Round-trip: state -> density matrix -> partial trace -> entropy
  agrees with state -> SVD -> entropy.

Quantum information theory has fewer single-number reference
values than the GR phases, so verification is mostly self-
consistency among definitions and reproduction of textbook
canonical examples.
"""

import math

import numpy as np
import pytest

from spacetime_lab.entropy import (
    density_matrix,
    entanglement_entropy,
    is_density_matrix,
    is_pure,
    mutual_information,
    partial_trace,
    schmidt_decomposition,
    schmidt_rank,
    von_neumann_entropy,
)


# ─────────────────────────────────────────────────────────────────────
# density_matrix and predicates
# ─────────────────────────────────────────────────────────────────────


class TestDensityMatrix:
    def test_pure_state_makes_rank_1_matrix(self):
        psi = np.array([1.0, 0.0, 0.0, 0.0])
        rho = density_matrix(psi)
        assert rho.shape == (4, 4)
        assert np.linalg.matrix_rank(rho) == 1

    def test_normalises_input(self):
        psi = np.array([2.0, 0.0])  # not normalised
        rho = density_matrix(psi)
        assert math.isclose(np.trace(rho).real, 1.0)
        assert math.isclose(rho[0, 0].real, 1.0)

    def test_zero_norm_raises(self):
        with pytest.raises(ValueError):
            density_matrix(np.zeros(4))

    def test_complex_input(self):
        psi = np.array([1.0 + 1.0j, 1.0 - 1.0j]) / 2.0
        rho = density_matrix(psi)
        # Hermitian
        assert np.allclose(rho, rho.conj().T)
        # Trace 1
        assert math.isclose(np.trace(rho).real, 1.0)


class TestPredicates:
    def test_is_pure_for_bell_pair(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        assert is_pure(density_matrix(bell))

    def test_is_pure_false_for_mixed(self):
        rho = np.eye(4) / 4  # maximally mixed
        assert not is_pure(rho)

    def test_is_density_matrix_valid(self):
        assert is_density_matrix(np.eye(2) / 2)
        assert is_density_matrix(density_matrix([1, 0, 0, 1]))

    def test_is_density_matrix_invalid_trace(self):
        bad = np.eye(3)  # trace 3, not 1
        assert not is_density_matrix(bad)

    def test_is_density_matrix_non_square(self):
        bad = np.zeros((2, 3))
        assert not is_density_matrix(bad)

    def test_is_density_matrix_not_psd(self):
        bad = np.diag([1.5, -0.5])  # trace 1, hermitian, but not PSD
        assert not is_density_matrix(bad)


# ─────────────────────────────────────────────────────────────────────
# partial_trace
# ─────────────────────────────────────────────────────────────────────


class TestPartialTrace:
    def test_bell_pair_traces_to_max_mixed(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        rho = density_matrix(bell)
        rho_A = partial_trace(rho, dims=(2, 2), traced_subsystems=(1,))
        np.testing.assert_allclose(rho_A, np.eye(2) / 2, atol=1e-12)

    def test_product_state_traces_correctly(self):
        psi = np.kron([1, 0], [1 / math.sqrt(2), 1 / math.sqrt(2)])
        rho = density_matrix(psi)
        rho_A = partial_trace(rho, dims=(2, 2), traced_subsystems=(1,))
        # Should be |0><0|
        expected = np.array([[1, 0], [0, 0]], dtype=complex)
        np.testing.assert_allclose(rho_A, expected, atol=1e-12)

    def test_partial_trace_three_qubit_ghz(self):
        ghz = np.zeros(8)
        ghz[0] = 1.0
        ghz[7] = 1.0
        ghz = ghz / math.sqrt(2)
        rho = density_matrix(ghz)
        # Trace out the middle qubit
        rho_02 = partial_trace(rho, dims=(2, 2, 2), traced_subsystems=(1,))
        # Result is the (0, 2)-marginal: 4x4
        assert rho_02.shape == (4, 4)
        assert math.isclose(np.trace(rho_02).real, 1.0)

    def test_dim_mismatch_raises(self):
        rho = np.eye(4) / 4
        with pytest.raises(ValueError):
            partial_trace(rho, dims=(3, 2), traced_subsystems=(0,))

    def test_traced_index_out_of_range_raises(self):
        rho = np.eye(4) / 4
        with pytest.raises(ValueError):
            partial_trace(rho, dims=(2, 2), traced_subsystems=(5,))

    def test_duplicate_traced_indices_raises(self):
        rho = np.eye(4) / 4
        with pytest.raises(ValueError):
            partial_trace(rho, dims=(2, 2), traced_subsystems=(0, 0))

    def test_trace_preserved(self):
        """Partial trace should preserve trace = 1."""
        psi = np.random.randn(8) + 1j * np.random.randn(8)
        psi = psi / np.linalg.norm(psi)
        rho = density_matrix(psi)
        for traced in [(0,), (1,), (2,), (0, 1), (0, 2), (1, 2)]:
            reduced = partial_trace(rho, dims=(2, 2, 2), traced_subsystems=traced)
            assert math.isclose(np.trace(reduced).real, 1.0, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# von_neumann_entropy
# ─────────────────────────────────────────────────────────────────────


class TestVonNeumannEntropy:
    def test_pure_state_zero(self):
        for psi in [
            np.array([1.0, 0.0]),
            np.array([1.0, 0.0, 0.0, 0.0]),
            np.array([0.6, 0.8, 0.0, 0.0]),  # pure but not basis vector
        ]:
            S = von_neumann_entropy(density_matrix(psi))
            assert abs(S) < 1e-12

    @pytest.mark.parametrize("d", [2, 3, 4, 5, 8, 16])
    def test_max_mixed_log_d(self, d):
        S = von_neumann_entropy(np.eye(d) / d)
        assert math.isclose(S, math.log(d), abs_tol=1e-12)

    def test_max_mixed_in_bits(self):
        S = von_neumann_entropy(np.eye(8) / 8, base="2")
        assert math.isclose(S, 3.0, abs_tol=1e-12)  # log_2(8) = 3

    def test_max_mixed_in_log10(self):
        S = von_neumann_entropy(np.eye(10) / 10, base="10")
        assert math.isclose(S, 1.0, abs_tol=1e-12)  # log10(10) = 1

    def test_invalid_base_raises(self):
        with pytest.raises(ValueError):
            von_neumann_entropy(np.eye(2) / 2, base="3")

    def test_unitary_invariance(self):
        """S(U rho U^dag) = S(rho) for any unitary U."""
        rho = np.diag([0.5, 0.3, 0.2])
        # Random unitary via QR decomposition
        rng = np.random.default_rng(42)
        A = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
        U, _ = np.linalg.qr(A)
        rho_rotated = U @ rho @ U.conj().T
        assert math.isclose(
            von_neumann_entropy(rho), von_neumann_entropy(rho_rotated), abs_tol=1e-12
        )

    def test_additivity(self):
        """S(rho_A x rho_B) = S(rho_A) + S(rho_B) for product states."""
        rho_A = np.diag([0.6, 0.4])
        rho_B = np.diag([0.5, 0.3, 0.2])
        rho_AB = np.kron(rho_A, rho_B)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho_AB)
        assert math.isclose(S_A + S_B, S_AB, abs_tol=1e-12)

    def test_handles_zero_eigenvalues(self):
        """0 log 0 = 0 convention."""
        rho = np.diag([1.0, 0.0, 0.0])
        S = von_neumann_entropy(rho)
        assert math.isclose(S, 0.0, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Schmidt decomposition
# ─────────────────────────────────────────────────────────────────────


class TestSchmidtDecomposition:
    def test_bell_pair_schmidt(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        coeffs, U, V = schmidt_decomposition(bell, dims=(2, 2))
        # Two Schmidt coefficients each equal to 1/sqrt(2)
        assert len(coeffs) == 2
        np.testing.assert_allclose(
            sorted(coeffs), [1 / math.sqrt(2), 1 / math.sqrt(2)]
        )

    def test_product_state_has_one_coefficient(self):
        prod = np.kron([1, 0], [1, 0])
        coeffs, _, _ = schmidt_decomposition(prod, dims=(2, 2))
        # Largest coefficient is 1, rest are 0
        assert math.isclose(coeffs[0], 1.0, abs_tol=1e-12)
        for c in coeffs[1:]:
            assert math.isclose(c, 0.0, abs_tol=1e-12)

    def test_coefficients_sum_squared_to_one(self):
        rng = np.random.default_rng(0)
        psi = rng.standard_normal(12) + 1j * rng.standard_normal(12)
        psi = psi / np.linalg.norm(psi)
        coeffs, _, _ = schmidt_decomposition(psi, dims=(3, 4))
        assert math.isclose(np.sum(coeffs ** 2), 1.0, abs_tol=1e-12)

    def test_reconstruction_from_schmidt(self):
        """sum_i lambda_i |u_i>|v_i> recovers the original state."""
        rng = np.random.default_rng(7)
        psi = rng.standard_normal(6) + 1j * rng.standard_normal(6)
        psi = psi / np.linalg.norm(psi)
        coeffs, U, V = schmidt_decomposition(psi, dims=(2, 3))
        recon = sum(
            coeffs[i] * np.kron(U[:, i], V[:, i]) for i in range(len(coeffs))
        )
        # Recon may differ from psi by an overall phase, so compare
        # |<psi | recon>|^2 = 1.
        overlap = abs(np.vdot(psi, recon)) ** 2
        assert math.isclose(overlap, 1.0, abs_tol=1e-10)

    def test_dim_mismatch_raises(self):
        with pytest.raises(ValueError):
            schmidt_decomposition(np.array([1, 0, 0]), dims=(2, 2))

    def test_zero_norm_raises(self):
        with pytest.raises(ValueError):
            schmidt_decomposition(np.zeros(4), dims=(2, 2))


class TestSchmidtRank:
    def test_bell_pair_rank_2(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        assert schmidt_rank(bell, dims=(2, 2)) == 2

    def test_product_state_rank_1(self):
        prod = np.kron([1, 0], [0, 1])
        assert schmidt_rank(prod, dims=(2, 2)) == 1

    @pytest.mark.parametrize("d", [2, 3, 4])
    def test_max_entangled_state_full_rank(self, d):
        """The maximally entangled state on d x d has Schmidt rank d."""
        state = np.zeros(d * d)
        for i in range(d):
            state[i * d + i] = 1.0
        state = state / math.sqrt(d)
        assert schmidt_rank(state, dims=(d, d)) == d


# ─────────────────────────────────────────────────────────────────────
# entanglement_entropy
# ─────────────────────────────────────────────────────────────────────


class TestEntanglementEntropy:
    def test_bell_pair_log_2(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        S = entanglement_entropy(bell, dims=(2, 2))
        assert math.isclose(S, math.log(2), abs_tol=1e-12)

    def test_bell_pair_in_bits(self):
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        S = entanglement_entropy(bell, dims=(2, 2), base="2")
        assert math.isclose(S, 1.0, abs_tol=1e-12)

    def test_product_state_zero(self):
        prod = np.kron([1, 0], [0, 1])
        S = entanglement_entropy(prod, dims=(2, 2))
        assert math.isclose(S, 0.0, abs_tol=1e-12)

    @pytest.mark.parametrize("d", [2, 3, 4, 5])
    def test_max_entangled_log_d(self, d):
        """Maximally entangled state on d x d has S = log d."""
        state = np.zeros(d * d)
        for i in range(d):
            state[i * d + i] = 1.0
        state = state / math.sqrt(d)
        S = entanglement_entropy(state, dims=(d, d))
        assert math.isclose(S, math.log(d), abs_tol=1e-12)

    def test_agreement_with_density_matrix_route(self):
        """state -> SVD -> entropy should equal state -> partial_trace -> S."""
        rng = np.random.default_rng(11)
        psi = rng.standard_normal(12) + 1j * rng.standard_normal(12)
        psi = psi / np.linalg.norm(psi)
        S_svd = entanglement_entropy(psi, dims=(3, 4))
        rho = density_matrix(psi)
        rho_A = partial_trace(rho, dims=(3, 4), traced_subsystems=(1,))
        S_pt = von_neumann_entropy(rho_A)
        assert math.isclose(S_svd, S_pt, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# GHZ — every bipartition gives log 2
# ─────────────────────────────────────────────────────────────────────


class TestGHZ:
    def setup_method(self):
        self.ghz = np.zeros(8)
        self.ghz[0] = 1.0
        self.ghz[7] = 1.0
        self.ghz = self.ghz / math.sqrt(2)
        self.rho = density_matrix(self.ghz)

    def test_qubit_0_vs_rest(self):
        rho_0 = partial_trace(self.rho, dims=(2, 2, 2), traced_subsystems=(1, 2))
        assert math.isclose(von_neumann_entropy(rho_0), math.log(2), abs_tol=1e-12)

    def test_qubit_1_vs_rest(self):
        rho_1 = partial_trace(self.rho, dims=(2, 2, 2), traced_subsystems=(0, 2))
        assert math.isclose(von_neumann_entropy(rho_1), math.log(2), abs_tol=1e-12)

    def test_qubit_2_vs_rest(self):
        rho_2 = partial_trace(self.rho, dims=(2, 2, 2), traced_subsystems=(0, 1))
        assert math.isclose(von_neumann_entropy(rho_2), math.log(2), abs_tol=1e-12)

    def test_pair_01_vs_qubit_2(self):
        rho_01 = partial_trace(self.rho, dims=(2, 2, 2), traced_subsystems=(2,))
        # Should also give log 2 — by Schmidt symmetry on the pure state
        assert math.isclose(von_neumann_entropy(rho_01), math.log(2), abs_tol=1e-12)

    def test_no_entanglement_after_tracing_one_qubit(self):
        """Tracing out one qubit of GHZ leaves a separable mixed state."""
        rho_01 = partial_trace(self.rho, dims=(2, 2, 2), traced_subsystems=(2,))
        # Half is |00><00| + half is |11><11|, no superposition.  Off-
        # diagonal entries should be zero.
        assert math.isclose(rho_01[0, 3].real, 0.0, abs_tol=1e-12)
        assert math.isclose(rho_01[3, 0].real, 0.0, abs_tol=1e-12)


# ─────────────────────────────────────────────────────────────────────
# Mutual information
# ─────────────────────────────────────────────────────────────────────


class TestMutualInformation:
    def test_bell_pair_mutual_info_is_2_log_2(self):
        """For a pure entangled state, I(A:B) = 2 S(rho_A) = 2 log 2."""
        bell = np.array([1, 0, 0, 1]) / math.sqrt(2)
        rho = density_matrix(bell)
        I = mutual_information(rho, dims=(2, 2), subsystem_A=(0,), subsystem_B=(1,))
        assert math.isclose(I, 2 * math.log(2), abs_tol=1e-12)

    def test_product_state_zero_mutual_info(self):
        prod = np.kron([1, 0], [0, 1])
        rho = density_matrix(prod)
        I = mutual_information(rho, dims=(2, 2), subsystem_A=(0,), subsystem_B=(1,))
        assert math.isclose(I, 0.0, abs_tol=1e-12)

    def test_overlapping_subsystems_raises(self):
        rho = np.eye(8) / 8
        with pytest.raises(ValueError):
            mutual_information(
                rho, dims=(2, 2, 2), subsystem_A=(0, 1), subsystem_B=(1, 2)
            )

    def test_mutual_info_non_negative(self):
        """I(A:B) >= 0 always (this is the strong subadditivity bound)."""
        rng = np.random.default_rng(123)
        psi = rng.standard_normal(8) + 1j * rng.standard_normal(8)
        psi = psi / np.linalg.norm(psi)
        rho = density_matrix(psi)
        for A, B in [((0,), (1,)), ((0,), (2,)), ((1,), (2,))]:
            I = mutual_information(rho, dims=(2, 2, 2), subsystem_A=A, subsystem_B=B)
            assert I >= -1e-12
