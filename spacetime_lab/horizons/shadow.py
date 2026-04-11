r"""Bardeen 1973 photon shadow of a Kerr black hole.

The photon shadow is the dark region in a distant observer's image
plane corresponding to photons that get captured by the black hole.
For a stationary, axially symmetric BH the shadow boundary is the
projection of the *spherical photon orbits* onto the observer's
image plane.

For Kerr in Boyer-Lindquist coordinates, the spherical photon orbits
are unstable circular null orbits at constant :math:`r = r_p`.  Each
:math:`r_p` in :math:`[r_p^-, r_p^+]` (the prograde and retrograde
equatorial photon-sphere radii) corresponds to a specific pair
:math:`(\xi, \eta)` of conserved impact parameters:

.. math::

    \xi(r_p) &= \frac{L_z}{E} = -\frac{r_p^3 - 3 M r_p^2 + a^2 r_p + a^2 M}{a (r_p - M)}, \\
    \eta(r_p) &= \frac{\mathcal{Q}}{E^2} = -\frac{r_p^3 (r_p^3 - 6 M r_p^2 + 9 M^2 r_p - 4 a^2 M)}{a^2 (r_p - M)^2}.

These map to the observer's image plane via Bardeen's celestial
coordinates :math:`(\alpha, \beta)`:

.. math::

    \alpha = -\xi \csc\theta_o, \qquad
    \beta = \pm\sqrt{\eta + a^2 \cos^2\theta_o - \xi^2 \cot^2\theta_o},

where :math:`\theta_o` is the polar inclination of the observer
relative to the BH spin axis.

For an **equatorial observer** (:math:`\theta_o = \pi/2`, the EHT
geometry for both M87* and Sgr A*), the formulas simplify to

.. math::

    \alpha(r_p) = -\xi(r_p), \qquad \beta(r_p) = \pm\sqrt{\eta(r_p)},

and the shadow boundary is the curve traced out by varying :math:`r_p`
between the two equatorial photon-sphere radii.

In the **Schwarzschild limit** :math:`a \to 0`, both :math:`\xi` and
:math:`\eta` become indeterminate but :math:`\xi^2 + \eta \to 27 M^2`,
so :math:`\alpha^2 + \beta^2 = 27 M^2`, giving the textbook circle of
radius :math:`b_\text{crit} = 3\sqrt{3}\,M \approx 5.196\,M`.

References
----------
- Bardeen, *Timelike and null geodesics in the Kerr metric*, in
  *Black Holes (Les Astres Occlus)*, ed. C. DeWitt and B. S.
  DeWitt, Gordon & Breach, 1973, pp. 215-239.
- Stein, L. C., *Kerr Spherical Photon Orbits*, online tool,
  https://duetosymmetry.com/tool/kerr-circular-photon-orbits/
- Cunha, Herdeiro et al, *Curvature radius and Kerr black hole
  shadow*, arXiv:1904.07710, eqs. (2.11)-(2.12).

The implementation here uses the standard sign conventions of those
references and has been verified against the Schwarzschild limit
:math:`b_\text{crit} = 3\sqrt{3}\,M`.
"""

from __future__ import annotations

import math

import numpy as np


def spherical_photon_orbit_xi(r_p: float, mass: float, spin: float) -> float:
    r"""Return :math:`\xi = L_z / E` of a Kerr spherical photon orbit at radius :math:`r_p`.

    Parameters
    ----------
    r_p : float
        Radius of the spherical photon orbit (in geometric units of
        ``mass``).  Must satisfy ``r_p > r_+``, the outer horizon.
    mass : float
        BH mass :math:`M`.
    spin : float
        BH spin parameter :math:`a`, with :math:`0 < a \le M`.  This
        function is **only valid for non-zero spin**; the
        Schwarzschild limit is degenerate (every :math:`r_p` on the
        photon sphere has the same :math:`b = 3\sqrt{3}\,M` and the
        formula's denominator vanishes).

    Returns
    -------
    float
        The conserved impact parameter :math:`\xi`.

    Raises
    ------
    ValueError
        If ``spin == 0``.
    """
    if spin == 0:
        raise ValueError(
            "spherical_photon_orbit_xi(spin=0) is undefined; the "
            "Schwarzschild limit is degenerate.  Use the closed-form "
            "circle b_crit = 3 sqrt(3) M instead."
        )
    M, a = float(mass), float(spin)
    r = float(r_p)
    return -((r**3 - 3 * M * r**2 + a**2 * r + a**2 * M) / (a * (r - M)))


def spherical_photon_orbit_eta(r_p: float, mass: float, spin: float) -> float:
    r"""Return :math:`\eta = \mathcal{Q} / E^2` of a Kerr spherical photon orbit at radius :math:`r_p`.

    See :func:`spherical_photon_orbit_xi` for parameter conventions.

    Returns
    -------
    float
        The conserved impact parameter :math:`\eta`.  Non-negative
        on the physically allowed range :math:`r_p \in [r_p^-, r_p^+]`
        of equatorial photon-sphere radii (it equals zero at the
        endpoints, the equatorial circular photon orbits themselves).
    """
    if spin == 0:
        raise ValueError(
            "spherical_photon_orbit_eta(spin=0) is undefined; the "
            "Schwarzschild limit is degenerate."
        )
    M, a = float(mass), float(spin)
    r = float(r_p)
    return -((r**3 * (r**3 - 6 * M * r**2 + 9 * M**2 * r - 4 * a**2 * M)) / (
        a**2 * (r - M) ** 2
    ))


def kerr_critical_curve_xi_eta(
    mass: float,
    spin: float,
    n_points: int = 200,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r"""Sample the conserved-quantity curve :math:`(\xi(r_p), \eta(r_p))`.

    Returns the impact parameters traced out by varying the spherical
    photon orbit radius :math:`r_p` between its prograde and
    retrograde extremes.  These extremes are the equatorial
    photon-sphere radii :math:`r_p^\pm`, where :math:`\eta = 0`.

    Parameters
    ----------
    mass : float
        BH mass.
    spin : float
        BH spin parameter, :math:`0 < a \le M`.
    n_points : int
        Number of samples along the curve.  Default 200.

    Returns
    -------
    r_p_array, xi_array, eta_array : numpy.ndarray
        Arrays of length ``n_points``, sampled uniformly in
        :math:`r_p` between the two equatorial photon-sphere radii.
    """
    if spin == 0:
        raise ValueError("kerr_critical_curve_xi_eta(spin=0) is undefined.")
    if spin > mass:
        raise ValueError(f"spin must be <= mass, got spin={spin}, mass={mass}")
    M, a = float(mass), float(spin)

    # Equatorial photon-sphere radii (Bardeen-Press-Teukolsky form,
    # already verified in Phase 3).  Prograde is smaller, retrograde
    # is larger.
    r_p_pro = 2.0 * M * (1.0 + math.cos((2.0 / 3.0) * math.acos(-a / M)))
    r_p_retro = 2.0 * M * (1.0 + math.cos((2.0 / 3.0) * math.acos(+a / M)))

    r_p = np.linspace(r_p_pro, r_p_retro, n_points)
    xi = np.array([spherical_photon_orbit_xi(r, M, a) for r in r_p])
    eta = np.array([spherical_photon_orbit_eta(r, M, a) for r in r_p])
    return r_p, xi, eta


def photon_shadow_kerr(
    spin: float,
    mass: float = 1.0,
    n_points: int = 400,
    inclination: float = math.pi / 2,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Return the Bardeen 1973 shadow boundary of a Kerr black hole.

    Constructs the closed curve :math:`(\alpha, \beta)` traced out in
    the observer's image plane by the spherical photon orbits, using
    the parametric formulas

    .. math::

        \alpha(r_p) = -\xi(r_p) \csc\theta_o, \qquad
        \beta(r_p) = \pm\sqrt{\eta(r_p) + a^2 \cos^2\theta_o
                              - \xi(r_p)^2 \cot^2\theta_o}.

    The result is the full closed curve (upper and lower halves
    concatenated, returning to the starting point).  Length is
    ``2 * n_points`` (one half-curve for :math:`\beta > 0`, one for
    :math:`\beta < 0`).

    Parameters
    ----------
    spin : float
        BH spin parameter :math:`a`, with :math:`0 < a \le M`.  The
        Schwarzschild case (``spin = 0``) is degenerate and is not
        handled here; the shadow is then a circle of radius
        :math:`3\sqrt{3}\,M` and can be drawn directly.
    mass : float
        BH mass :math:`M`.  Defaults to ``1``.
    n_points : int
        Number of points along the half-curve.  Default ``400``.
    inclination : float
        Polar inclination angle :math:`\theta_o` of the observer in
        radians.  Defaults to :math:`\pi/2` (equatorial observer,
        the EHT geometry for both M87* and Sgr A*).  Currently only
        ``inclination = pi/2`` is fully tested; the general formula
        is implemented but the test suite only pins the equatorial
        case to known closed-form values.

    Returns
    -------
    alpha, beta : numpy.ndarray
        Arrays of length ``2 * n_points`` giving the closed shadow
        boundary in the observer's image plane.

    Raises
    ------
    ValueError
        If ``spin == 0`` (use the analytic Schwarzschild circle
        instead) or if ``spin > mass``.

    Examples
    --------
    Equatorial observer of an extremal Kerr BH::

        alpha, beta = photon_shadow_kerr(spin=0.998)

        # Plot the closed curve
        import matplotlib.pyplot as plt
        plt.fill(alpha, beta, color='#222', alpha=0.5)
        plt.gca().set_aspect('equal')
    """
    if spin == 0:
        raise ValueError(
            "photon_shadow_kerr requires spin > 0.  For Schwarzschild, "
            "the shadow is a circle of radius 3 sqrt(3) M and can be "
            "drawn analytically."
        )
    if spin > mass:
        raise ValueError(f"spin must be <= mass, got spin={spin}, mass={mass}")

    r_p, xi, eta = kerr_critical_curve_xi_eta(mass, spin, n_points)

    cos_theta_o = math.cos(inclination)
    sin_theta_o = math.sin(inclination)
    cot_theta_o = cos_theta_o / sin_theta_o
    csc_theta_o = 1.0 / sin_theta_o
    a = float(spin)

    alpha_arr = -xi * csc_theta_o
    beta_squared = eta + a * a * cos_theta_o**2 - xi**2 * cot_theta_o**2
    # Numerical noise can give tiny negative values right at the
    # endpoints r_p = r_p_pro and r_p = r_p_retro where eta = 0
    # exactly.  Clip to zero so the sqrt is defined.
    beta_squared = np.maximum(beta_squared, 0.0)
    beta_arr = np.sqrt(beta_squared)

    # Build the closed curve: upper half forward, lower half reversed.
    alpha_full = np.concatenate([alpha_arr, alpha_arr[::-1]])
    beta_full = np.concatenate([beta_arr, -beta_arr[::-1]])
    return alpha_full, beta_full
