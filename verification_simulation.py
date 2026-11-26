"""
Vérification numérique des lois géométriques (MGD / MGI) et génération des figures SVG
======================================================================================
Exécution :
    python verification_simulation.py

Génère :
  - Un bilan chiffré dans la console (tests aléatoires 2D/3D, fermeture du parallélogramme,
    suivi d'une trajectoire circulaire et d'une trajectoire 3D).
  - 3 figures vectorielles SVG dans ./figures/ :
      1. schema_cinematique.svg
      2. espace_travail_et_trajectoire.svg
      3. verification_trajectoire_angles.svg
"""

import math
import os
import random
from typing import List, Tuple

from modele_geometrique import (
    ParametresBras,
    mgd_2d,
    mgd_3d,
    mgi_2d,
    mgi_3d,
    verifier_fermeture_parallelogramme,
)


# ---------------------------------------------------------------------------
# 1. TESTS NUMÉRIQUES DE VÉRIFICATION
# ---------------------------------------------------------------------------

def test_aller_retour_aleatoire(params: ParametresBras, n_points: int = 10000) -> dict:
    """
    Tire n_points configurations articulaires (theta0, theta1, theta2) dans le
    domaine admissible, calcule X = MGD(q), puis q_calc = MGI(X) et X_verif = MGD(q_calc).
    """
    rng = random.Random(42)
    max_err_pos_3d = 0.0
    max_err_angle_deg = 0.0
    max_err_fermeture = 0.0
    nb_tests = 0

    while nb_tests < n_points:
        t0 = math.radians(rng.uniform(params.theta0_min_deg, params.theta0_max_deg))
        t1 = math.radians(rng.uniform(params.theta1_min_deg, params.theta1_max_deg))
        t2 = math.radians(rng.uniform(params.theta2_min_deg, params.theta2_max_deg))
        ok, _ = params.est_dans_butees(t1, t2, t0)
        if not ok:
            continue

        pts_2d = mgd_2d(t1, t2, params)
        # Ignorer les points à r <= 0 (non physiques côté arrière)
        if pts_2d["E"][0] <= 1.0:
            continue

        ferm = verifier_fermeture_parallelogramme(pts_2d, params)
        max_err_fermeture = max(max_err_fermeture, max(ferm.values()))

        pts_3d = mgd_3d(t0, t1, t2, params)
        xE, yE, zE = pts_3d["E"]

        t0_c, t1_c, t2_c = mgi_3d(xE, yE, zE, params=params, config="coude_haut")
        pts_3d_verif = mgd_3d(t0_c, t1_c, t2_c, params)
        xv, yv, zv = pts_3d_verif["E"]

        err_pos = math.sqrt((xv - xE) ** 2 + (yv - yE) ** 2 + (zv - zE) ** 2)
        err_ang = max(
            abs(math.degrees(math.atan2(math.sin(t0_c - t0), math.cos(t0_c - t0)))),
            abs(math.degrees(t1_c - t1)),
            abs(math.degrees(t2_c - t2)),
        )

        max_err_pos_3d = max(max_err_pos_3d, err_pos)
        max_err_angle_deg = max(max_err_angle_deg, err_ang)
        nb_tests += 1

    return {
        "nb_points": nb_tests,
        "max_err_pos_mm": max_err_pos_3d,
        "max_err_angle_deg": max_err_angle_deg,
        "max_err_fermeture": max_err_fermeture,
    }


def simuler_trajectoire_cercle(
    params: ParametresBras,
    centre_r: float = 240.0,
    centre_z: float = 160.0,
    rayon: float = 55.0,
    n_pas: int = 120,
) -> List[dict]:
    """
    Simule le suivi d'une trajectoire circulaire dans le plan (r, z)
    et enregistre à chaque pas les angles MGI et l'erreur MGD(MGI(cible)).
    """
    historique = []
    for k in range(n_pas + 1):
        u = 2.0 * math.pi * k / n_pas
        r_cible = centre_r + rayon * math.cos(u)
        z_cible = centre_z + rayon * math.sin(u)

        t1, t2 = mgi_2d(r_cible, z_cible, params=params, config="coude_haut", verifier_butees=True)
        pts = mgd_2d(t1, t2, params)
        r_reel, z_reel = pts["E"]
        err = math.hypot(r_reel - r_cible, z_reel - z_cible)

        historique.append({
            "t": k / n_pas,
            "r_cible": r_cible,
            "z_cible": z_cible,
            "r_reel": r_reel,
            "z_reel": z_reel,
            "theta1_deg": math.degrees(t1),
            "theta2_deg": math.degrees(t2),
            "alpha_deg": math.degrees(t1 - t2),
            "err_mm": err,
            "pts": pts,
        })
    return historique


# ---------------------------------------------------------------------------
# 2. GÉNÉRATION DES FIGURES SVG (ZÉRO DÉPENDANCE EXTERNE)
# ---------------------------------------------------------------------------

def _svg_header(w: int, h: int, title: str) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f"  <title>{title}</title>",
        "  <defs>",
        '    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#334155"/>',
        "    </marker>",
        '    <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>',
        "    </marker>",
        '    <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '      <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669"/>',
        "    </marker>",
        "  </defs>",
        f'  <rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
    ]


def _arc_svg(cx: float, cy: float, radius: float, ang1_deg: float, ang2_deg: float) -> str:
    """Arc SVG dans un repère où y pointe vers le bas (angles trigonométriques en degrés)."""
    a1 = math.radians(ang1_deg)
    a2 = math.radians(ang2_deg)
    x1, y1 = cx + radius * math.cos(a1), cy - radius * math.sin(a1)
    x2, y2 = cx + radius * math.cos(a2), cy - radius * math.sin(a2)
    diff = ang2_deg - ang1_deg
    large_arc = 1 if abs(diff) > 180 else 0
    sweep = 0 if diff > 0 else 1
    return f"M {x1:.1f} {y1:.1f} A {radius:.1f} {radius:.1f} 0 {large_arc} {sweep} {x2:.1f} {y2:.1f}"


def generer_schema_cinematique_svg(path: str, params: ParametresBras) -> None:
    """Génère un schéma cinématique clair et coté du bras à parallélogramme."""
    w, h = 920, 620
    scale = 1.45
    ox, oy = 270.0, 520.0  # Position pixel de O0 = (0, 0)

    def to_px(pt: Tuple[float, float]) -> Tuple[float, float]:
        return ox + pt[0] * scale, oy - pt[1] * scale

    t1 = math.radians(72.0)
    t2 = math.radians(-18.0)
    pts = mgd_2d(t1, t2, params)
    pO0, pO, pA, pB, pC, pE = (to_px(pts[k]) for k in ("O0", "O", "A", "B", "C", "E"))

    lines = _svg_header(w, h, "Schéma cinématique du bras à parallélogramme")

    # Titre
    lines.append('  <text x="460" y="34" text-anchor="middle" font-family="Segoe UI, Arial" font-size="20" font-weight="bold" fill="#0f172a">Schéma cinématique — Bras manipulateur à parallélogramme (OABC)</text>')
    lines.append('  <text x="460" y="56" text-anchor="middle" font-family="Segoe UI, Arial" font-size="13" fill="#475569">Plan vertical (O₀, u_r, z₀) — M1 entraîne Bras 1 (θ₁), M2 entraîne Manivelle (OC) → Bielle (CB) → Bras 2 (θ₂)</text>')

    # Sol / châssis rover
    lines.append(f'  <line x1="80" y1="{oy:.1f}" x2="840" y2="{oy:.1f}" stroke="#94a3b8" stroke-width="2"/>')
    for gx in range(90, 840, 22):
        lines.append(f'  <line x1="{gx}" y1="{oy:.1f}" x2="{gx-10}" y2="{oy+12:.1f}" stroke="#cbd5e1" stroke-width="1.5"/>')

    # Axes repère R0 / R1
    lines.append(f'  <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{ox+480:.1f}" y2="{oy:.1f}" stroke="#334155" stroke-width="1.8" marker-end="url(#arrow)"/>')
    lines.append(f'  <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{ox:.1f}" y2="85" stroke="#334155" stroke-width="1.8" marker-end="url(#arrow)"/>')
    lines.append(f'  <text x="{ox+490:.1f}" y="{oy+5:.1f}" font-family="Segoe UI, Arial" font-size="15" font-weight="bold" fill="#334155">u_r (r)</text>')
    lines.append(f'  <text x="{ox-26:.1f}" y="92" font-family="Segoe UI, Arial" font-size="15" font-weight="bold" fill="#334155">z₀</text>')

    # Horizontales de référence en O et en A (pointillés)
    lines.append(f'  <line x1="{pO[0]-120:.1f}" y1="{pO[1]:.1f}" x2="{pO[0]+180:.1f}" y2="{pO[1]:.1f}" stroke="#94a3b8" stroke-dasharray="6,4" stroke-width="1.3"/>')
    lines.append(f'  <line x1="{pA[0]-40:.1f}" y1="{pA[1]:.1f}" x2="{pA[0]+180:.1f}" y2="{pA[1]:.1f}" stroke="#94a3b8" stroke-dasharray="6,4" stroke-width="1.3"/>')

    # Socle base O0 -> O
    lines.append(f'  <rect x="{ox-28:.1f}" y="{pO[1]:.1f}" width="56" height="{oy-pO[1]:.1f}" fill="#e2e8f0" stroke="#475569" stroke-width="2" rx="4"/>')
    lines.append(f'  <text x="{ox-78:.1f}" y="{(oy+pO[1])/2+5:.1f}" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#334155">h₀ = {params.h0:.0f}</text>')

    # Bielle C -> B (orange)
    lines.append(f'  <line x1="{pC[0]:.1f}" y1="{pC[1]:.1f}" x2="{pB[0]:.1f}" y2="{pB[1]:.1f}" stroke="#f59e0b" stroke-width="7" stroke-linecap="round"/>')
    # Manivelle O -> C (violet)
    lines.append(f'  <line x1="{pO[0]:.1f}" y1="{pO[1]:.1f}" x2="{pC[0]:.1f}" y2="{pC[1]:.1f}" stroke="#7c3aed" stroke-width="8" stroke-linecap="round"/>')
    # Bras 1 O -> A (bleu)
    lines.append(f'  <line x1="{pO[0]:.1f}" y1="{pO[1]:.1f}" x2="{pA[0]:.1f}" y2="{pA[1]:.1f}" stroke="#2563eb" stroke-width="10" stroke-linecap="round"/>')
    # Bras 2 B -> A -> E (vert)
    lines.append(f'  <line x1="{pB[0]:.1f}" y1="{pB[1]:.1f}" x2="{pE[0]:.1f}" y2="{pE[1]:.1f}" stroke="#059669" stroke-width="10" stroke-linecap="round"/>')

    # Arcs d'angles theta1 et theta2
    lines.append(f'  <path d="{_arc_svg(pO[0], pO[1], 62, 0, 72)}" fill="none" stroke="#2563eb" stroke-width="2.2" marker-end="url(#arrow-blue)"/>')
    lines.append(f'  <text x="{pO[0]+54:.1f}" y="{pO[1]-40:.1f}" font-family="Segoe UI, Arial" font-size="16" font-weight="bold" fill="#2563eb">θ₁</text>')

    lines.append(f'  <path d="{_arc_svg(pA[0], pA[1], 72, 0, -18)}" fill="none" stroke="#059669" stroke-width="2.2" marker-end="url(#arrow-green)"/>')
    lines.append(f'  <text x="{pA[0]+80:.1f}" y="{pA[1]+22:.1f}" font-family="Segoe UI, Arial" font-size="16" font-weight="bold" fill="#059669">θ₂</text>')

    # Articulations (pivots)
    for nom, pt, col, dx, dy in [
        ("O₀ (base)", pO0, "#334155", 10, 22),
        ("O (M1, M2)", pO, "#0f172a", -105, 22),
        ("A (coude)", pA, "#0f172a", -10, -18),
        ("B (talon)", pB, "#059669", -78, -10),
        ("C (manivelle)", pC, "#7c3aed", -115, 5),
        ("E (effecteur)", pE, "#dc2626", 12, 6),
    ]:
        lines.append(f'  <circle cx="{pt[0]:.1f}" cy="{pt[1]:.1f}" r="6.5" fill="#ffffff" stroke="{col}" stroke-width="3"/>')
        lines.append(f'  <text x="{pt[0]+dx:.1f}" y="{pt[1]+dy:.1f}" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="{col}">{nom}</text>')

    # Annotations des longueurs
    mid_OA = ((pO[0] + pA[0]) / 2 + 16, (pO[1] + pA[1]) / 2 + 6)
    mid_CB = ((pC[0] + pB[0]) / 2 - 76, (pC[1] + pB[1]) / 2)
    mid_AE = ((pA[0] + pE[0]) / 2 + 4, (pA[1] + pE[1]) / 2 - 14)
    mid_OC = ((pO[0] + pC[0]) / 2 - 16, (pO[1] + pC[1]) / 2 + 24)
    mid_AB = ((pA[0] + pB[0]) / 2 - 10, (pA[1] + pB[1]) / 2 - 18)

    lines.append(f'  <text x="{mid_OA[0]:.1f}" y="{mid_OA[1]:.1f}" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#1d4ed8">Bras 1 (L₁)</text>')
    lines.append(f'  <text x="{mid_CB[0]:.1f}" y="{mid_CB[1]:.1f}" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#d97706">Bielle (b=L₁)</text>')
    lines.append(f'  <text x="{mid_AE[0]:.1f}" y="{mid_AE[1]:.1f}" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#047857">Bras 2 (L₂)</text>')
    lines.append(f'  <text x="{mid_OC[0]:.1f}" y="{mid_OC[1]:.1f}" font-family="Segoe UI, Arial" font-size="13" font-weight="bold" fill="#6d28d9">a</text>')
    lines.append(f'  <text x="{mid_AB[0]:.1f}" y="{mid_AB[1]:.1f}" font-family="Segoe UI, Arial" font-size="13" font-weight="bold" fill="#047857">a</text>')

    # Encadré synthèse des équations
    lines.append('  <rect x="615" y="88" width="280" height="175" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" rx="8"/>')
    lines.append('  <text x="630" y="114" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#0f172a">Fermeture parallélogramme :</text>')
    lines.append('  <text x="630" y="136" font-family="Consolas, monospace" font-size="12.5" fill="#334155">OA = CB = L₁  et  OC = AB = a</text>')
    lines.append('  <text x="630" y="156" font-family="Consolas, monospace" font-size="12.5" fill="#334155">⇒ AB = OC  ⇒  orientation(AE) = θ₂</text>')
    lines.append('  <text x="630" y="186" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#0f172a">Modèle Géométrique Direct :</text>')
    lines.append('  <text x="630" y="208" font-family="Consolas, monospace" font-size="12.5" fill="#1e293b">r_E = L₁·cos(θ₁) + L₂·cos(θ₂)</text>')
    lines.append('  <text x="630" y="228" font-family="Consolas, monospace" font-size="12.5" fill="#1e293b">z_E = h₀ + L₁·sin(θ₁) + L₂·sin(θ₂)</text>')
    lines.append('  <text x="630" y="248" font-family="Consolas, monospace" font-size="12" fill="#475569">x_E = r_E·cos(θ₀), y_E = r_E·sin(θ₀)</text>')

    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generer_espace_travail_svg(
    path: str,
    params: ParametresBras,
    traj: List[dict],
) -> None:
    """Génère la carte de l'espace de travail (r, z) et la trajectoire vérifiée."""
    w, h = 900, 600
    r_min, r_max = -100.0, 440.0
    z_min, z_max = -60.0, 420.0
    pad_l, pad_r, pad_t, pad_b = 75, 40, 60, 60

    sx = (w - pad_l - pad_r) / (r_max - r_min)
    sy = (h - pad_t - pad_b) / (z_max - z_min)
    s = min(sx, sy)

    def to_px(r: float, z: float) -> Tuple[float, float]:
        return pad_l + (r - r_min) * s, h - pad_b - (z - z_min) * s

    lines = _svg_header(w, h, "Espace de travail et suivi de trajectoire")
    lines.append('  <text x="450" y="34" text-anchor="middle" font-family="Segoe UI, Arial" font-size="19" font-weight="bold" fill="#0f172a">Espace de travail atteignable (plan r, z) et vérification de trajectoire</text>')

    # Grille
    for r_val in range(-50, 450, 50):
        px, _ = to_px(r_val, 0)
        lines.append(f'  <line x1="{px:.1f}" y1="{pad_t}" x2="{px:.1f}" y2="{h-pad_b}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'  <text x="{px:.1f}" y="{h-pad_b+20}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="11" fill="#64748b">{r_val}</text>')
    for z_val in range(-50, 450, 50):
        _, py = to_px(0, z_val)
        lines.append(f'  <line x1="{pad_l}" y1="{py:.1f}" x2="{w-pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'  <text x="{pad_l-10}" y="{py+4:.1f}" text-anchor="end" font-family="Segoe UI, Arial" font-size="11" fill="#64748b">{z_val}</text>')

    # Nuage de points de l'espace de travail
    for t1_d in range(int(params.theta1_min_deg), int(params.theta1_max_deg) + 1, 4):
        for t2_d in range(int(params.theta2_min_deg), int(params.theta2_max_deg) + 1, 4):
            alpha = t1_d - t2_d
            if not (params.alpha_min_deg <= alpha <= params.alpha_max_deg):
                continue
            pts = mgd_2d(math.radians(t1_d), math.radians(t2_d), params)
            px, py = to_px(*pts["E"])
            lines.append(f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="2.2" fill="#93c5fd" opacity="0.55"/>')

    # Poses intermédiaires du bras sur la trajectoire
    for idx in (0, len(traj) // 4, len(traj) // 2, 3 * len(traj) // 4):
        pts = traj[idx]["pts"]
        pO, pA, pB, pC, pE = (to_px(*pts[k]) for k in ("O", "A", "B", "C", "E"))
        op = "0.9" if idx == 0 else "0.28"
        lines.append(f'  <g opacity="{op}">')
        lines.append(f'    <line x1="{pO[0]:.1f}" y1="{pO[1]:.1f}" x2="{pC[0]:.1f}" y2="{pC[1]:.1f}" stroke="#7c3aed" stroke-width="3.5"/>')
        lines.append(f'    <line x1="{pC[0]:.1f}" y1="{pC[1]:.1f}" x2="{pB[0]:.1f}" y2="{pB[1]:.1f}" stroke="#f59e0b" stroke-width="3.5"/>')
        lines.append(f'    <line x1="{pO[0]:.1f}" y1="{pO[1]:.1f}" x2="{pA[0]:.1f}" y2="{pA[1]:.1f}" stroke="#2563eb" stroke-width="5"/>')
        lines.append(f'    <line x1="{pB[0]:.1f}" y1="{pB[1]:.1f}" x2="{pE[0]:.1f}" y2="{pE[1]:.1f}" stroke="#059669" stroke-width="5"/>')
        lines.append("  </g>")

    # Trajectoire cible vs MGD(MGI)
    pts_cible = " ".join(f"{to_px(d['r_cible'], d['z_cible'])[0]:.1f},{to_px(d['r_cible'], d['z_cible'])[1]:.1f}" for d in traj)
    pts_reel = " ".join(f"{to_px(d['r_reel'], d['z_reel'])[0]:.1f},{to_px(d['r_reel'], d['z_reel'])[1]:.1f}" for d in traj)
    lines.append(f'  <polyline points="{pts_cible}" fill="none" stroke="#dc2626" stroke-width="4" opacity="0.45"/>')
    lines.append(f'  <polyline points="{pts_reel}" fill="none" stroke="#0f172a" stroke-width="1.8" stroke-dasharray="5,3"/>')

    # Axes labels & légende
    lines.append(f'  <text x="{w/2:.1f}" y="{h-16}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#334155">Portée radiale r (mm)</text>')
    lines.append(f'  <text x="24" y="{h/2:.1f}" text-anchor="middle" transform="rotate(-90 24 {h/2:.1f})" font-family="Segoe UI, Arial" font-size="14" font-weight="bold" fill="#334155">Hauteur z (mm)</text>')

    lines.append('  <rect x="615" y="72" width="240" height="106" fill="#ffffff" stroke="#cbd5e1" rx="6" opacity="0.95"/>')
    lines.append('  <circle cx="634" cy="94" r="5" fill="#93c5fd"/>')
    lines.append('  <text x="648" y="98" font-family="Segoe UI, Arial" font-size="12" fill="#1e293b">Espace de travail (butées actives)</text>')
    lines.append('  <line x1="624" y1="120" x2="644" y2="120" stroke="#dc2626" stroke-width="4" opacity="0.5"/>')
    lines.append('  <text x="648" y="124" font-family="Segoe UI, Arial" font-size="12" fill="#1e293b">Trajectoire cible (cercle R=55 mm)</text>')
    lines.append('  <line x1="624" y1="146" x2="644" y2="146" stroke="#0f172a" stroke-width="2" stroke-dasharray="5,3"/>')
    lines.append('  <text x="648" y="150" font-family="Segoe UI, Arial" font-size="12" fill="#1e293b">Trajectoire reconstruite MGD(MGI)</text>')

    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generer_courbes_angles_svg(path: str, traj: List[dict]) -> None:
    """Génère les courbes d'évolution des angles moteurs theta1(t), theta2(t), alpha(t)."""
    w, h = 900, 460
    pad_l, pad_r, pad_t, pad_b = 75, 40, 60, 65
    y_min, y_max = -90.0, 150.0

    def to_px(t: float, deg: float) -> Tuple[float, float]:
        x = pad_l + t * (w - pad_l - pad_r)
        y = h - pad_b - ((deg - y_min) / (y_max - y_min)) * (h - pad_t - pad_b)
        return x, y

    lines = _svg_header(w, h, "Évolution des angles moteurs sur la trajectoire")
    lines.append('  <text x="450" y="34" text-anchor="middle" font-family="Segoe UI, Arial" font-size="18" font-weight="bold" fill="#0f172a">Consignes articulaires calculées par le MGI sur la trajectoire circulaire</text>')

    for deg in range(-90, 151, 30):
        _, py = to_px(0, deg)
        stroke = "#94a3b8" if deg == 0 else "#e2e8f0"
        lines.append(f'  <line x1="{pad_l}" y1="{py:.1f}" x2="{w-pad_r}" y2="{py:.1f}" stroke="{stroke}" stroke-width="1"/>')
        lines.append(f'  <text x="{pad_l-10}" y="{py+4:.1f}" text-anchor="end" font-family="Segoe UI, Arial" font-size="11" fill="#64748b">{deg}°</text>')

    for i in range(0, 11):
        t = i / 10.0
        px, _ = to_px(t, 0)
        lines.append(f'  <line x1="{px:.1f}" y1="{pad_t}" x2="{px:.1f}" y2="{h-pad_b}" stroke="#e2e8f0" stroke-width="1"/>')
        lines.append(f'  <text x="{px:.1f}" y="{h-pad_b+20}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="11" fill="#64748b">{t:.1f}</text>')

    for key, col in [("theta1_deg", "#2563eb"), ("theta2_deg", "#059669"), ("alpha_deg", "#d97706")]:
        pts_str = " ".join(f"{to_px(d['t'], d[key])[0]:.1f},{to_px(d['t'], d[key])[1]:.1f}" for d in traj)
        lines.append(f'  <polyline points="{pts_str}" fill="none" stroke="{col}" stroke-width="2.6"/>')

    max_err = max(d["err_mm"] for d in traj)
    lines.append(f'  <text x="{w/2:.1f}" y="{h-18}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="13" font-weight="bold" fill="#334155">Temps normalisé t/T  —  Erreur max ||MGD(MGI(X)) - X|| = {max_err:.2e} mm</text>')
    lines.append(f'  <text x="24" y="{h/2:.1f}" text-anchor="middle" transform="rotate(-90 24 {h/2:.1f})" font-family="Segoe UI, Arial" font-size="13" font-weight="bold" fill="#334155">Angle (degrés)</text>')

    # Légende
    lines.append('  <rect x="670" y="72" width="180" height="82" fill="#ffffff" stroke="#cbd5e1" rx="6"/>')
    for idx, (lbl, col) in enumerate([("θ₁ (Bras 1)", "#2563eb"), ("θ₂ (Bras 2)", "#059669"), ("α = θ₁ - θ₂", "#d97706")]):
        yy = 94 + idx * 22
        lines.append(f'  <line x1="684" y1="{yy}" x2="708" y2="{yy}" stroke="{col}" stroke-width="3"/>')
        lines.append(f'  <text x="716" y="{yy+4}" font-family="Segoe UI, Arial" font-size="12" fill="#1e293b">{lbl}</text>')

    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    params = ParametresBras()
    print("=" * 72)
    print("VÉRIFICATION DES LOIS GÉOMÉTRIQUES DU BRAS À PARALLÉLOGRAMME")
    print("=" * 72)
    print(f"Paramètres : L1={params.L1} mm, L2={params.L2} mm, a={params.a} mm, b={params.b} mm, h0={params.h0} mm")

    # 1. Test sur 10 000 configurations aléatoires 3D
    res = test_aller_retour_aleatoire(params, n_points=10000)
    print(f"\n[1] Test Monte-Carlo MGD -> MGI -> MGD ({res['nb_points']} points 3D) :")
    print(f"    - Erreur max de position 3D           : {res['max_err_pos_mm']:.3e} mm")
    print(f"    - Erreur max sur les angles (θ0,θ1,θ2): {res['max_err_angle_deg']:.3e} °")
    print(f"    - Erreur max fermeture parallélogramme: {res['max_err_fermeture']:.3e}")
    assert res["max_err_pos_mm"] < 1e-10, "Erreur de position trop élevée !"
    assert res["max_err_angle_deg"] < 1e-10, "Erreur angulaire trop élevée !"
    assert res["max_err_fermeture"] < 1e-12, "Fermeture du parallélogramme non respectée !"

    # 2. Test sur une trajectoire circulaire dans le plan (r, z)
    traj = simuler_trajectoire_cercle(params)
    max_err_traj = max(d["err_mm"] for d in traj)
    t1_vals = [d["theta1_deg"] for d in traj]
    t2_vals = [d["theta2_deg"] for d in traj]
    print(f"\n[2] Test suivi de trajectoire circulaire ({len(traj)} points, R=55 mm) :")
    print(f"    - Plage θ₁ : [{min(t1_vals):.2f}°, {max(t1_vals):.2f}°]")
    print(f"    - Plage θ₂ : [{min(t2_vals):.2f}°, {max(t2_vals):.2f}°]")
    print(f"    - Erreur max de suivi MGD(MGI(cible)) : {max_err_traj:.3e} mm")
    assert max_err_traj < 1e-10

    # 3. Génération des figures SVG
    fig_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
    os.makedirs(fig_dir, exist_ok=True)
    f1 = os.path.join(fig_dir, "schema_cinematique.svg")
    f2 = os.path.join(fig_dir, "espace_travail_et_trajectoire.svg")
    f3 = os.path.join(fig_dir, "verification_trajectoire_angles.svg")

    generer_schema_cinematique_svg(f1, params)
    generer_espace_travail_svg(f2, params, traj)
    generer_courbes_angles_svg(f3, traj)

    print("\n[3] Figures SVG générées avec succès :")
    print(f"    - {f1}")
    print(f"    - {f2}")
    print(f"    - {f3}")
    print("\nTOUTES LES VÉRIFICATIONS SONT PASSÉES AVEC SUCCÈS.")


if __name__ == "__main__":
    main()
