"""
Modèle géométrique (MGD & MGI) d'un bras manipulateur à parallélogramme (3 DDL)
================================================================================
Architecture correspondant au prototype SolidWorks :
  - Base rotative optionnelle autour de z0 : angle theta0 (0 rad en mode plan 2 DDL)
  - Moteur 1 (NEMA 17) à l'épaule O : entraîne Bras 1 (OA, longueur L1), angle theta1
  - Moteur 2 (NEMA 17) coaxial en O : entraîne la Manivelle (OC, longueur a)
  - Bielle (CB, longueur b = L1) reliant la Manivelle au talon B de Bras 2 (AB = a)
  - Bras 2 (AE, longueur L2) portant l'effecteur E, orienté selon l'angle absolu theta2

Convention des angles dans le plan vertical (O, u_r, z0) :
  - theta1 : angle (u_r, OA) mesuré positivement de l'horizontale vers le haut (rad)
  - theta2 : angle absolu (u_r, AE) de Bras 2 (rad)
    Note : la manivelle OC pointe vers l'arrière dans la direction theta2 + pi,
    de sorte que OC = AB = -a * u2 et CB = OA (parallélogramme OABC).
"""

from dataclasses import dataclass
import math
from typing import Dict, Optional, Tuple


@dataclass
class ParametresBras:
    """Paramètres géométriques et butées articulaires du bras (en mm et degrés)."""

    # --- Cotes géométriques (à ajuster selon vos pièces SolidWorks) ---
    L1: float = 200.0   # Longueur de Bras 1 (entraxe OA) [mm]
    L2: float = 200.0   # Longueur de Bras 2 (entraxe AE) [mm]
    a: float = 60.0     # Longueur de la Manivelle (OC) et du talon arrière de Bras 2 (AB) [mm]
    h0: float = 80.0    # Hauteur de l'axe d'épaule O par rapport à la base O0 [mm]

    # --- Butées articulaires (fins de course & sécurité mécanique) [degrés] ---
    theta0_min_deg: float = -180.0
    theta0_max_deg: float = 180.0
    theta1_min_deg: float = 15.0
    theta1_max_deg: float = 135.0
    theta2_min_deg: float = -75.0
    theta2_max_deg: float = 60.0

    # --- Limites de l'angle relatif alpha = theta1 - theta2 (évite les singularités) [degrés] ---
    alpha_min_deg: float = 20.0
    alpha_max_deg: float = 155.0

    @property
    def b(self) -> float:
        """Longueur de la bielle CB = L1 (condition de parallélogramme)."""
        return self.L1

    def est_dans_butees(
        self,
        theta1: float,
        theta2: float,
        theta0: float = 0.0,
    ) -> Tuple[bool, str]:
        """Vérifie si une configuration articulaire respecte les fins de course."""
        t0 = math.degrees(theta0)
        t1 = math.degrees(theta1)
        t2 = math.degrees(theta2)
        alpha = t1 - t2

        if not (self.theta0_min_deg - 1e-6 <= t0 <= self.theta0_max_deg + 1e-6):
            return False, f"theta0={t0:.1f}° hors limites [{self.theta0_min_deg}, {self.theta0_max_deg}]°"
        if not (self.theta1_min_deg - 1e-6 <= t1 <= self.theta1_max_deg + 1e-6):
            return False, f"theta1={t1:.1f}° hors limites [{self.theta1_min_deg}, {self.theta1_max_deg}]°"
        if not (self.theta2_min_deg - 1e-6 <= t2 <= self.theta2_max_deg + 1e-6):
            return False, f"theta2={t2:.1f}° hors limites [{self.theta2_min_deg}, {self.theta2_max_deg}]°"
        if not (self.alpha_min_deg - 1e-6 <= alpha <= self.alpha_max_deg + 1e-6):
            return False, f"alpha=theta1-theta2={alpha:.1f}° hors limites [{self.alpha_min_deg}, {self.alpha_max_deg}]°"
        return True, "OK"


def mgd_2d(
    theta1: float,
    theta2: float,
    params: ParametresBras = ParametresBras(),
) -> Dict[str, Tuple[float, float]]:
    """
    Modèle Géométrique Direct dans le plan vertical (r, z).

    Retourne les coordonnées (r, z) en mm de tous les points remarquables :
      - O0 : origine de la base (0, 0)
      - O  : axe d'épaule (moteurs M1 et M2)
      - A  : coude (articulation Bras 1 / Bras 2)
      - B  : talon arrière de Bras 2 (articulation Bielle / Bras 2)
      - C  : extrémité de la Manivelle (articulation Manivelle / Bielle)
      - E  : extrémité effectrice de Bras 2
    """
    c1, s1 = math.cos(theta1), math.sin(theta1)
    c2, s2 = math.cos(theta2), math.sin(theta2)

    O0 = (0.0, 0.0)
    O = (0.0, params.h0)
    A = (params.L1 * c1, params.h0 + params.L1 * s1)
    C = (-params.a * c2, params.h0 - params.a * s2)
    B = (A[0] - params.a * c2, A[1] - params.a * s2)
    E = (A[0] + params.L2 * c2, A[1] + params.L2 * s2)

    return {"O0": O0, "O": O, "A": A, "B": B, "C": C, "E": E}


def mgd_3d(
    theta0: float,
    theta1: float,
    theta2: float,
    params: ParametresBras = ParametresBras(),
) -> Dict[str, Tuple[float, float, float]]:
    """
    Modèle Géométrique Direct dans le repère 3D fixe R0 = (O0, x0, y0, z0).
    """
    pts_2d = mgd_2d(theta1, theta2, params)
    c0, s0 = math.cos(theta0), math.sin(theta0)
    return {
        nom: (r * c0, r * s0, z)
        for nom, (r, z) in pts_2d.items()
    }


def mgi_2d(
    r_E: float,
    z_E: float,
    params: ParametresBras = ParametresBras(),
    config: str = "coude_haut",
    verifier_butees: bool = False,
) -> Tuple[float, float]:
    """
    Modèle Géométrique Inverse dans le plan vertical (r, z).

    Paramètres
    ----------
    r_E, z_E : float
        Position cible de l'effecteur E dans le plan (r, z) [mm].
    params : ParametresBras
        Paramètres géométriques du bras.
    config : {"coude_haut", "coude_bas"}
        Choix de la branche analytique (coude_haut : alpha = theta1 - theta2 >= 0).
    verifier_butees : bool
        Si True, lève ValueError si la solution sort des butées de fins de course.

    Retourne
    --------
    (theta1, theta2) : Tuple[float, float] en radians.
    """
    if config not in ("coude_haut", "coude_bas"):
        raise ValueError("config doit être 'coude_haut' ou 'coude_bas'")

    z_p = z_E - params.h0
    d2 = r_E * r_E + z_p * z_p
    d = math.sqrt(d2)

    d_min = abs(params.L1 - params.L2)
    d_max = params.L1 + params.L2
    if d < d_min - 1e-9 or d > d_max + 1e-9:
        raise ValueError(
            f"Cible hors d'atteinte : d={d:.2f} mm hors [{d_min:.2f}, {d_max:.2f}] mm"
        )

    cos_alpha = (d2 - params.L1 ** 2 - params.L2 ** 2) / (2.0 * params.L1 * params.L2)
    cos_alpha = max(-1.0, min(1.0, cos_alpha))

    alpha = math.acos(cos_alpha)
    if config == "coude_bas":
        alpha = -alpha

    beta = math.atan2(z_p, r_E)
    gamma = math.atan2(params.L2 * math.sin(alpha), params.L1 + params.L2 * math.cos(alpha))

    theta1 = beta + gamma
    theta2 = theta1 - alpha

    if verifier_butees:
        ok, msg = params.est_dans_butees(theta1, theta2)
        if not ok:
            raise ValueError(f"Solution hors butées : {msg}")

    return theta1, theta2


def mgi_3d(
    x_E: float,
    y_E: float,
    z_E: float,
    params: ParametresBras = ParametresBras(),
    config: str = "coude_haut",
    theta0_courant: float = 0.0,
    verifier_butees: bool = False,
) -> Tuple[float, float, float]:
    """
    Modèle Géométrique Inverse dans le repère 3D fixe R0.

    Retourne (theta0, theta1, theta2) en radians.
    """
    r_E = math.hypot(x_E, y_E)
    if r_E < 1e-9:
        # Singularité d'épaule : l'effecteur est sur l'axe vertical z0
        theta0 = theta0_courant
    else:
        theta0 = math.atan2(y_E, x_E)

    theta1, theta2 = mgi_2d(
        r_E, z_E, params=params, config=config, verifier_butees=False
    )

    if verifier_butees:
        ok, msg = params.est_dans_butees(theta1, theta2, theta0)
        if not ok:
            raise ValueError(f"Solution hors butées : {msg}")

    return theta0, theta1, theta2


def verifier_fermeture_parallelogramme(
    pts_2d: Dict[str, Tuple[float, float]],
    params: ParametresBras = ParametresBras(),
) -> Dict[str, float]:
    """
    Vérifie numériquement la fermeture géométrique de la boucle OABC
    et les longueurs de tous les segments rigides du mécanisme.
    """
    def dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def vec(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
        return (p2[0] - p1[0], p2[1] - p1[1])

    O, A, B, C, E = pts_2d["O"], pts_2d["A"], pts_2d["B"], pts_2d["C"], pts_2d["E"]
    vOA = vec(O, A)
    vCB = vec(C, B)
    vOC = vec(O, C)
    vAB = vec(A, B)

    # Produits vectoriels normalisés (nuls si les barres opposées sont parallèles)
    cross_bras_bielle = abs(vOA[0] * vCB[1] - vOA[1] * vCB[0]) / (params.L1 ** 2)
    cross_maniv_talon = abs(vOC[0] * vAB[1] - vOC[1] * vAB[0]) / (params.a ** 2)

    return {
        "err_L1_OA": abs(dist(O, A) - params.L1),
        "err_b_CB": abs(dist(C, B) - params.b),
        "err_a_OC": abs(dist(O, C) - params.a),
        "err_a_AB": abs(dist(A, B) - params.a),
        "err_L2_AE": abs(dist(A, E) - params.L2),
        "err_parallelisme_OA_CB": cross_bras_bielle,
        "err_parallelisme_OC_AB": cross_maniv_talon,
    }


def angle_manivelle_moteur(theta2: float) -> float:
    """Retourne l'angle géométrique (u_r, OC) de la manivelle (en rad)."""
    return theta2 + math.pi
