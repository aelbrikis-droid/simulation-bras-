"""
Simulateur interactif du bras manipulateur à parallélogramme (Tkinter - sans dépendance)
========================================================================================
Exécution :
    python simulateur_interactif.py

Fonctionnalités :
  - Mode MGD : pilotage par curseurs (θ₀, θ₁, θ₂) et affichage des coordonnées (x, y, z)
  - Mode MGI : clic direct sur le graphique (ou curseurs r_E, z_E) pour calculer (θ₁, θ₂)
  - Choix Coude Haut / Coude Bas
  - Animation d'une trajectoire circulaire avec vérification temps réel de l'erreur MGD <-> MGI
"""

import math
import tkinter as tk
from tkinter import ttk

from modele_geometrique import ParametresBras, mgd_2d, mgd_3d, mgi_2d


class SimulateurBrasApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Simulateur — Lois géométriques du bras à parallélogramme")
        self.geometry("1120x680")
        self.configure(bg="#f8fafc")

        self.params = ParametresBras()
        self.en_animation = False
        self.anim_step = 0
        self.trace_pts = []

        # Dimensions du canvas (plan r, z)
        self.cw, self.ch = 740, 620
        self.scale = 1.28
        self.ox, self.oy = 175.0, 520.0  # Pixel correspondant à O0 = (0, 0)

        self._construire_interface()
        self._dessiner_fond_statique()
        self._maj_depuis_mgd()

    def to_px(self, r: float, z: float):
        return self.ox + r * self.scale, self.oy - z * self.scale

    def to_world(self, px: float, py: float):
        return (px - self.ox) / self.scale, (self.oy - py) / self.scale

    def _construire_interface(self) -> None:
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Canvas à gauche
        self.canvas = tk.Canvas(
            main, width=self.cw, height=self.ch, bg="#ffffff",
            highlightthickness=1, highlightbackground="#cbd5e1"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 12))
        self.canvas.bind("<Button-1>", self._clic_canvas)
        self.canvas.bind("<B1-Motion>", self._clic_canvas)

        # Panneau de contrôle à droite
        ctrl = ttk.Frame(main, width=340)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

        ttk.Label(ctrl, text="Pilotage & Vérification", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        # --- Section MGD ---
        f_mgd = ttk.LabelFrame(ctrl, text="Mode MGD (Angles moteurs)", padding=8)
        f_mgd.pack(fill=tk.X, pady=4)

        self.var_t0 = tk.DoubleVar(value=0.0)
        self.var_t1 = tk.DoubleVar(value=72.0)
        self.var_t2 = tk.DoubleVar(value=-18.0)

        self._ajouter_slider(f_mgd, "θ₀ Base (°)", self.var_t0, -180, 180, self._maj_depuis_mgd)
        self._ajouter_slider(f_mgd, "θ₁ Bras 1 (°)", self.var_t1, self.params.theta1_min_deg, self.params.theta1_max_deg, self._maj_depuis_mgd)
        self._ajouter_slider(f_mgd, "θ₂ Bras 2 (°)", self.var_t2, self.params.theta2_min_deg, self.params.theta2_max_deg, self._maj_depuis_mgd)

        # --- Section MGI ---
        f_mgi = ttk.LabelFrame(ctrl, text="Mode MGI (Cible ou clic sur la vue)", padding=8)
        f_mgi.pack(fill=tk.X, pady=6)

        self.var_r = tk.DoubleVar(value=252.0)
        self.var_z = tk.DoubleVar(value=208.0)
        self.var_cfg = tk.StringVar(value="coude_haut")

        self._ajouter_slider(f_mgi, "r_E cible (mm)", self.var_r, 40, 395, self._maj_depuis_mgi)
        self._ajouter_slider(f_mgi, "z_E cible (mm)", self.var_z, -40, 440, self._maj_depuis_mgi)

        rb_frame = ttk.Frame(f_mgi)
        rb_frame.pack(fill=tk.X, pady=(4, 0))
        ttk.Radiobutton(rb_frame, text="Coude haut", variable=self.var_cfg, value="coude_haut", command=self._maj_depuis_mgi).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(rb_frame, text="Coude bas", variable=self.var_cfg, value="coude_bas", command=self._maj_depuis_mgi).pack(side=tk.LEFT, padx=4)

        # --- Animation ---
        f_anim = ttk.LabelFrame(ctrl, text="Vérification sur trajectoire", padding=8)
        f_anim.pack(fill=tk.X, pady=6)
        self.btn_anim = ttk.Button(f_anim, text="Lancer / Arrêter cercle (R=55 mm)", command=self._basculer_animation)
        self.btn_anim.pack(fill=tk.X)

        # --- Télémetrie ---
        f_info = ttk.LabelFrame(ctrl, text="Résultats numériques", padding=8)
        f_info.pack(fill=tk.BOTH, expand=True, pady=6)
        self.lbl_info = tk.Label(
            f_info, justify=tk.LEFT, anchor="nw",
            font=("Consolas", 9.5), bg="#ffffff", fg="#0f172a", padx=8, pady=8
        )
        self.lbl_info.pack(fill=tk.BOTH, expand=True)

    def _ajouter_slider(self, parent, texte, var, vmin, vmax, cmd):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=texte, width=15).pack(side=tk.LEFT)
        val_lbl = ttk.Label(row, text=f"{var.get():.1f}", width=6)
        val_lbl.pack(side=tk.RIGHT)

        def on_move(_):
            val_lbl.config(text=f"{var.get():.1f}")
            cmd()

        s = ttk.Scale(row, from_=vmin, to=vmax, variable=var, orient=tk.HORIZONTAL, command=on_move)
        s.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        var._val_lbl = val_lbl

    def _dessiner_fond_statique(self) -> None:
        # Grille 50 mm
        for r in range(-100, 450, 50):
            x, _ = self.to_px(r, 0)
            self.canvas.create_line(x, 20, x, self.ch - 20, fill="#f1f5f9", tags="fond")
        for z in range(-50, 450, 50):
            _, y = self.to_px(0, z)
            self.canvas.create_line(20, y, self.cw - 20, y, fill="#f1f5f9", tags="fond")

        # Espace de travail admissible
        for t1_d in range(int(self.params.theta1_min_deg), int(self.params.theta1_max_deg) + 1, 5):
            for t2_d in range(int(self.params.theta2_min_deg), int(self.params.theta2_max_deg) + 1, 5):
                if self.params.alpha_min_deg <= (t1_d - t2_d) <= self.params.alpha_max_deg:
                    pts = mgd_2d(math.radians(t1_d), math.radians(t2_d), self.params)
                    px, py = self.to_px(*pts["E"])
                    self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill="#dbeafe", outline="", tags="fond")

        # Sol et axes
        self.canvas.create_line(20, self.oy, self.cw - 20, self.oy, fill="#64748b", width=2, tags="fond")
        self.canvas.create_line(self.ox, self.ch - 20, self.ox, 20, fill="#64748b", width=1.5, dash=(4, 4), tags="fond")
        self.canvas.create_text(self.cw - 40, self.oy - 12, text="r (mm)", fill="#334155", font=("Segoe UI", 10, "bold"), tags="fond")
        self.canvas.create_text(self.ox + 26, 30, text="z (mm)", fill="#334155", font=("Segoe UI", 10, "bold"), tags="fond")

        # Socle
        xO, yO = self.to_px(0, self.params.h0)
        self.canvas.create_rectangle(self.ox - 20, yO, self.ox + 20, self.oy, fill="#e2e8f0", outline="#475569", width=2, tags="fond")

    def _dessiner_bras(self, t0: float, t1: float, t2: float, err_mgi: float = 0.0, statut: str = "OK") -> None:
        self.canvas.delete("bras")
        pts = mgd_2d(t1, t2, self.params)
        pts3 = mgd_3d(t0, t1, t2, self.params)

        pO, pA, pB, pC, pE = (self.to_px(*pts[k]) for k in ("O", "A", "B", "C", "E"))

        # Trace de l'animation
        if len(self.trace_pts) >= 2:
            coords = [c for pt in self.trace_pts for c in self.to_px(*pt)]
            self.canvas.create_line(*coords, fill="#dc2626", width=2, tags="bras")

        # Barres
        self.canvas.create_line(*pO, *pC, fill="#7c3aed", width=6, capstyle=tk.ROUND, tags="bras")
        self.canvas.create_line(*pC, *pB, fill="#f59e0b", width=6, capstyle=tk.ROUND, tags="bras")
        self.canvas.create_line(*pO, *pA, fill="#2563eb", width=8, capstyle=tk.ROUND, tags="bras")
        self.canvas.create_line(*pB, *pE, fill="#059669", width=8, capstyle=tk.ROUND, tags="bras")

        # Pivots
        for nom, pt, col in [("O", pO, "#0f172a"), ("A", pA, "#0f172a"), ("B", pB, "#059669"), ("C", pC, "#7c3aed"), ("E", pE, "#dc2626")]:
            self.canvas.create_oval(pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5, fill="#ffffff", outline=col, width=2.5, tags="bras")
            self.canvas.create_text(pt[0] + 12, pt[1] - 10, text=nom, fill=col, font=("Segoe UI", 10, "bold"), tags="bras")

        rE, zE = pts["E"]
        xE, yE, _ = pts3["E"]
        alpha_deg = math.degrees(t1 - t2)
        ok, msg = self.params.est_dans_butees(t1, t2, t0)

        txt = (
            f"--- Angles articulaires ---\n"
            f"θ₀ (base)    : {math.degrees(t0):7.2f} °\n"
            f"θ₁ (Bras 1)  : {math.degrees(t1):7.2f} °\n"
            f"θ₂ (Bras 2)  : {math.degrees(t2):7.2f} °\n"
            f"α = θ₁ - θ₂  : {alpha_deg:7.2f} °\n\n"
            f"--- Position effecteur E ---\n"
            f"r_E          : {rE:7.2f} mm\n"
            f"z_E          : {zE:7.2f} mm\n"
            f"x_E (3D)     : {xE:7.2f} mm\n"
            f"y_E (3D)     : {yE:7.2f} mm\n\n"
            f"--- Vérification ---\n"
            f"Err MGD↔MGI  : {err_mgi:.2e} mm\n"
            f"Butées       : {'OK' if ok else msg}\n"
            f"Statut MGI   : {statut}"
        )
        self.lbl_info.config(text=txt)

    def _maj_depuis_mgd(self) -> None:
        t0 = math.radians(self.var_t0.get())
        t1 = math.radians(self.var_t1.get())
        t2 = math.radians(self.var_t2.get())
        pts = mgd_2d(t1, t2, self.params)
        rE, zE = pts["E"]
        self.var_r.set(rE)
        self.var_z.set(zE)
        self.var_r._val_lbl.config(text=f"{rE:.1f}")
        self.var_z._val_lbl.config(text=f"{zE:.1f}")
        self._dessiner_bras(t0, t1, t2, err_mgi=0.0, statut="Mode MGD")

    def _maj_depuis_mgi(self) -> None:
        r_c = self.var_r.get()
        z_c = self.var_z.get()
        t0 = math.radians(self.var_t0.get())
        try:
            t1, t2 = mgi_2d(r_c, z_c, params=self.params, config=self.var_cfg.get())
            pts = mgd_2d(t1, t2, self.params)
            err = math.hypot(pts["E"][0] - r_c, pts["E"][1] - z_c)
            self.var_t1.set(math.degrees(t1))
            self.var_t2.set(math.degrees(t2))
            self.var_t1._val_lbl.config(text=f"{math.degrees(t1):.1f}")
            self.var_t2._val_lbl.config(text=f"{math.degrees(t2):.1f}")
            self._dessiner_bras(t0, t1, t2, err_mgi=err, statut="Cible atteinte")
        except ValueError as e:
            self.lbl_info.config(text=f"Cible (r={r_c:.1f}, z={z_c:.1f}) mm :\n{e}")

    def _clic_canvas(self, event) -> None:
        self.en_animation = False
        r_c, z_c = self.to_world(event.x, event.y)
        self.var_r.set(r_c)
        self.var_z.set(z_c)
        self.var_r._val_lbl.config(text=f"{r_c:.1f}")
        self.var_z._val_lbl.config(text=f"{z_c:.1f}")
        self._maj_depuis_mgi()

    def _basculer_animation(self) -> None:
        self.en_animation = not self.en_animation
        if self.en_animation:
            self.trace_pts = []
            self.anim_step = 0
            self._tick_animation()

    def _tick_animation(self) -> None:
        if not self.en_animation:
            return
        u = 2.0 * math.pi * (self.anim_step % 120) / 120.0
        r_c = 240.0 + 55.0 * math.cos(u)
        z_c = 160.0 + 55.0 * math.sin(u)
        self.trace_pts.append((r_c, z_c))
        if len(self.trace_pts) > 125:
            self.trace_pts.pop(0)
        self.var_r.set(r_c)
        self.var_z.set(z_c)
        self._maj_depuis_mgi()
        self.anim_step += 1
        self.after(25, self._tick_animation)


if __name__ == "__main__":
    app = SimulateurBrasApp()
    app.mainloop()
