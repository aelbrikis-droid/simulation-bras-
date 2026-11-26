# Lois géométriques du bras manipulateur à parallélogramme

## 1. Architecture mécanique du prototype

D'après l'assemblage SolidWorks (`Bras Prototype/Assemblage Bras Prototype.SLDASM`), le bras est un **manipulateur à parallélogramme déformable** piloté depuis l'épaule par deux moteurs pas à pas **NEMA 17** (avec rotation optionnelle de la base autour de l'axe vertical $\vec{z}_0$, soit **3 DDL** réductible à **2 DDL** dans le plan vertical lorsque $\theta_0 = 0$) :

- **Base (`la base de bras`)** : support fixe sur le châssis du rover, d'origine $O_0$, plaçant l'axe commun d'épaule $O$ à une hauteur $h_0$.
- **Moteur 1 (épaule)** : entraîne directement **`Bras 1`** (segment $OA$ de longueur $L_1$), repéré par l'angle $\theta_1$.
- **Moteur 2 (coaxial en $O$)** : entraîne la **`Manivelle`** (segment $OC$ de longueur $a$).
- **`Bielle`** (segment $CB$ de longueur $b = L_1$) : relie l'extrémité $C$ de la manivelle au talon arrière $B$ de **`Bras 2`**.
- **`Bras 2`** (pièce rigide $B - A - E$) : articulé en pivot au coude $A$, avec un prolongement arrière $AB = a$ et une partie avant $AE = L_2$ portant l'effecteur $E$.
- **Fins de course (`Fin De Course`, micro-switch V-156-1C25)** : assurent la prise d'origine (*homing*) des moteurs pas à pas et bornent le domaine articulaire.

---

## 2. Schéma cinématique et paramétrage

Voir le schéma vectoriel haute définition généré par la simulation : [`figures/schema_cinematique.svg`](figures/schema_cinematique.svg).

```text
                      z0
                      ^
                      |      B(talon)     A(coude)
                      |        o============o==============o E (effecteur)
                      |       /            / \    Bras 2 (L2)
                      |      / Bielle     /   \  theta2 (depuis l'horizontale)
                      |     /  (b = L1)  /     \
                      |    /            / Bras 1 (L1)
                      |   /            /
           C(maniv.)  o==/============o O (M1, M2)  --- theta1 --->
                  a   |  Manivelle    |
                      |               | h0 (base)
        --------------+---------------+-------------------------> u_r (r)
                                      O0 (châssis rover)
```

### Repères et variables

| Symbole | Description | Unité | Valeur par défaut |
| :--- | :--- | :---: | :---: |
| $\mathcal{R}_0 = (O_0, \vec{x}_0, \vec{y}_0, \vec{z}_0)$ | Repère fixe lié au châssis du rover | — | — |
| $\mathcal{R}_1 = (O, \vec{u}_r, \vec{u}_\theta, \vec{z}_0)$ | Repère tournant d'angle $\theta_0$ autour de $\vec{z}_0$ | — | — |
| $\theta_0$ | Angle de rotation de la base (optionnel, $0$ en mode plan) | rad | $[-180^\circ, +180^\circ]$ |
| $\theta_1$ | Angle de `Bras 1` : $\theta_1 = (\vec{u}_r, \overrightarrow{OA})$ | rad | $[15^\circ, 135^\circ]$ |
| $\theta_2$ | Angle absolu de `Bras 2` : $\theta_2 = (\vec{u}_r, \overrightarrow{AE})$ | rad | $[-75^\circ, 60^\circ]$ |
| $L_1$ | Entraxe de `Bras 1` ($OA$) | mm | $200$ |
| $L_2$ | Longueur utile de `Bras 2` ($AE$) | mm | $200$ |
| $a$ | Longueur de la `Manivelle` ($OC$) et du talon arrière ($AB$) | mm | $60$ |
| $b$ | Longueur de la `Bielle` ($CB$) | mm | $200$ ($= L_1$) |
| $h_0$ | Hauteur de l'axe d'épaule $O$ au-dessus de $O_0$ | mm | $80$ |

---

## 3. Démonstration des lois géométriques

### 3.1 Fermeture géométrique du parallélogramme $(OABC)$

Dans le plan vertical $(O, \vec{u}_r, \vec{z}_0)$, on note les vecteurs unitaires :
$$\vec{u}_1 = \cos\theta_1\,\vec{u}_r + \sin\theta_1\,\vec{z}_0, \qquad \vec{u}_2 = \cos\theta_2\,\vec{u}_r + \sin\theta_2\,\vec{z}_0$$

La boucle fermée $O \to A \to B \to C \to O$ s'écrit vectoriellement :
$$\overrightarrow{OA} + \overrightarrow{AB} = \overrightarrow{OC} + \overrightarrow{CB}$$

Par construction mécanique :
- $\|\overrightarrow{OA}\| = \|\overrightarrow{CB}\| = L_1$ (longueur de `Bras 1` égale à la longueur $b$ de la `Bielle`),
- $\|\overrightarrow{OC}\| = \|\overrightarrow{AB}\| = a$ (longueur de la `Manivelle` égale au talon arrière de `Bras 2`).

Dans la configuration non-croisée (garantie par les butées mécaniques), le quadrilatère $OABC$ est un **parallélogramme déformable**, ce qui impose :
$$\overrightarrow{AB} = \overrightarrow{OC} \qquad \text{et} \qquad \overrightarrow{CB} = \overrightarrow{OA}$$

Or `Bras 2` est une pièce rigide alignée ($B, A, E$ colinéaires, avec $B$ à l'arrière de $A$ et $E$ à l'avant), donc :
$$\overrightarrow{AB} = -a\,\vec{u}_2 \implies \overrightarrow{OC} = -a\,\vec{u}_2 = a\big(\cos(\theta_2 + \pi)\,\vec{u}_r + \sin(\theta_2 + \pi)\,\vec{z}_0\big)$$

**Propriété clé (découplage cinématique)** : l'orientation absolue $\theta_2$ de `Bras 2` dans le plan vertical dépend **uniquement** de la position du Moteur 2 (qui pilote la `Manivelle` $OC$), et reste **indépendante** de l'angle $\theta_1$ de `Bras 1` ! Cela simplifie fortement les équations par rapport à un bras série classique où l'angle absolu du second segment vaut $\theta_1 + \theta_2$.

---

### 3.2 Modèle Géométrique Direct (MGD)

L'objectif du MGD est de déterminer la position de l'effecteur $E$ à partir des coordonnées articulaires $\mathbf{q} = (\theta_0, \theta_1, \theta_2)^T$.

Dans le plan vertical $(O_0, \vec{u}_r, \vec{z}_0)$ :
$$\overrightarrow{O_0 E} = \overrightarrow{O_0 O} + \overrightarrow{OA} + \overrightarrow{AE} = h_0\,\vec{z}_0 + L_1\,\vec{u}_1 + L_2\,\vec{u}_2$$

En projetant sur $(\vec{u}_r, \vec{z}_0)$, on obtient le **MGD plan (2 DDL)** :
$$\begin{cases}
r_E = L_1 \cos\theta_1 + L_2 \cos\theta_2 \\
z_E = h_0 + L_1 \sin\theta_1 + L_2 \sin\theta_2
\end{cases}$$

En intégrant la rotation de la base $\theta_0$ autour de $\vec{z}_0$ ($\vec{u}_r = \cos\theta_0\,\vec{x}_0 + \sin\theta_0\,\vec{y}_0$), on obtient le **MGD spatial (3 DDL)** :
$$\begin{cases}
x_E = \big(L_1 \cos\theta_1 + L_2 \cos\theta_2\big)\cos\theta_0 \\
y_E = \big(L_1 \cos\theta_1 + L_2 \cos\theta_2\big)\sin\theta_0 \\
z_E = h_0 + L_1 \sin\theta_1 + L_2 \sin\theta_2
\end{cases}$$

---

### 3.3 Modèle Géométrique Inverse (MGI)

L'objectif du MGI est de calculer les consignes articulaires $(\theta_0, \theta_1, \theta_2)$ permettant d'atteindre une position cible $\mathbf{X}_E = (x_E, y_E, z_E)^T$.

#### Étape 1 : Angle de base $\theta_0$ et réduction dans le plan vertical
$$\theta_0 = \operatorname{atan2}(y_E, x_E), \qquad r_E = \sqrt{x_E^2 + y_E^2}, \qquad z'_E = z_E - h_0$$
*(Si $r_E = 0$, la cible est sur l'axe vertical $\vec{z}_0$ : singularité d'épaule, on conserve la valeur courante de $\theta_0$.)*

#### Étape 2 : Condition d'accessibilité géométrique
On note $d = \|\overrightarrow{OE}\| = \sqrt{r_E^2 + z'^2_E}$. D'après l'inégalité triangulaire dans le triangle $OAE$, la cible est géométriquement atteignable si et seulement si :
$$|L_1 - L_2| \le d \le L_1 + L_2$$

#### Étape 3 : Angle relatif au coude $\alpha = \theta_1 - \theta_2$ (loi des cosinus)
En élevant au carré les deux équations du MGD plan et en sommant :
$$r_E^2 + z'^2_E = L_1^2(\cos^2\theta_1 + \sin^2\theta_1) + L_2^2(\cos^2\theta_2 + \sin^2\theta_2) + 2 L_1 L_2 (\cos\theta_1\cos\theta_2 + \sin\theta_1\sin\theta_2)$$
Or $\cos\theta_1\cos\theta_2 + \sin\theta_1\sin\theta_2 = \cos(\theta_1 - \theta_2) = \cos\alpha$, d'où :
$$\cos\alpha = \frac{r_E^2 + z'^2_E - L_1^2 - L_2^2}{2 L_1 L_2} \in [-1, 1]$$

Deux configurations analytiques existent :
- **Coude en haut** (configuration nominale du bras manipulateur) : $\alpha = +\arccos(\cos\alpha) \in [0, \pi]$.
- **Coude en bas** : $\alpha = -\arccos(\cos\alpha) \in [-\pi, 0]$.

#### Étape 4 : Expressions explicites de $\theta_1$ et $\theta_2$
Notons $\beta = \operatorname{atan2}(z'_E, r_E)$ l'angle d'élévation du vecteur $\overrightarrow{OE}$.
En décomposant $\overrightarrow{OE} = L_1 \vec{u}_1 + L_2 \vec{u}_2$ dans le repère lié à `Bras 1` $(\vec{u}_1, \vec{u}_1^\perp)$, ses composantes sont :
$$\overrightarrow{OE}\cdot\vec{u}_1 = L_1 + L_2\cos(\theta_2 - \theta_1) = L_1 + L_2\cos\alpha$$
$$\overrightarrow{OE}\cdot\vec{u}_1^\perp = L_2\sin(\theta_2 - \theta_1) = -L_2\sin\alpha$$

L'angle orienté $(\vec{u}_1, \overrightarrow{OE}) = \beta - \theta_1$ vaut donc $-\operatorname{atan2}(L_2\sin\alpha,\; L_1 + L_2\cos\alpha)$. On en déduit immédiatement les lois inverses exactes :
$$\theta_1 = \operatorname{atan2}(z'_E, r_E) + \operatorname{atan2}\!\big(L_2 \sin\alpha,\; L_1 + L_2 \cos\alpha\big)$$
$$\theta_2 = \theta_1 - \alpha$$

#### Étape 5 : Singularités et contraintes mécaniques (fins de course)
- **Singularités de déploiement/repliement** : $\alpha = 0^\circ$ (bras totalement tendu) et $\alpha = 180^\circ$ (bras replié). Sur un mécanisme à parallélogramme, ces positions aplatissent le quadrilatère $OABC$ et font perdre la transmission d'effort par la bielle. On impose donc en pratique :
  $$\alpha_{\min} \le \theta_1 - \theta_2 \le \alpha_{\max} \qquad (\text{par défaut } 20^\circ \le \alpha \le 155^\circ)$$
- **Butées matérielles** : vérifiées par rapport aux fins de course ($\theta_1 \in [\theta_{1,\min}, \theta_{1,\max}]$ et $\theta_2 \in [\theta_{2,\min}, \theta_{2,\max}]$).

---

## 4. Vérification des lois sur simulation Python

Trois scripts Python (sans dépendance externe, exécutables directement avec Python 3.12) ont été développés :

1. [`modele_geometrique.py`](modele_geometrique.py) : implémentation complète de `ParametresBras`, `mgd_2d`, `mgd_3d`, `mgi_2d`, `mgi_3d` et `verifier_fermeture_parallelogramme`.
2. [`verification_simulation.py`](verification_simulation.py) : campagne de validation automatique et génération des figures SVG.
3. [`simulateur_interactif.py`](simulateur_interactif.py) : interface graphique interactive (`tkinter`) pour tester le MGD, le MGI (par curseurs ou clic direct) et l'animation de trajectoire.

### Résultats de la campagne de vérification (`python verification_simulation.py`)

Avec les paramètres par défaut ($L_1 = 200\text{ mm}$, $L_2 = 200\text{ mm}$, $a = 60\text{ mm}$, $b = 200\text{ mm}$, $h_0 = 80\text{ mm}$) :

| Test de vérification | Protocole | Résultat obtenu | Statut |
| :--- | :--- | :---: | :---: |
| **Cohérence MGD $\to$ MGI $\to$ MGD (position 3D)** | 10 000 poses aléatoires dans l'espace admissible | Erreur max $= 1{,}640 \times 10^{-13}\text{ mm}$ | Validé |
| **Cohérence angulaire $(\theta_0, \theta_1, \theta_2)$** | 10 000 poses aléatoires | Erreur max $= 8{,}269 \times 10^{-14}\ ^\circ$ | Validé |
| **Fermeture du parallélogramme $(OABC)$** | Conservation de $OA, CB, OC, AB, AE$ et parallélisme | Erreur max $= 8{,}527 \times 10^{-14}$ | Validé |
| **Suivi de trajectoire circulaire ($R = 55\text{ mm}$)** | 121 points, centre $(240, 160)\text{ mm}$ | Erreur max $= 8{,}527 \times 10^{-14}\text{ mm}$ | Validé |

### Figures générées

- **Schéma cinématique** : [`figures/schema_cinematique.svg`](figures/schema_cinematique.svg)
- **Espace de travail et trajectoire reconstruite** : [`figures/espace_travail_et_trajectoire.svg`](figures/espace_travail_et_trajectoire.svg)
- **Consignes articulaires $\theta_1(t), \theta_2(t), \alpha(t)$** : [`figures/verification_trajectoire_angles.svg`](figures/verification_trajectoire_angles.svg)

---

## 5. Adapter vos cotes SolidWorks et lancer la simulation

1. Ouvrez [`modele_geometrique.py`](modele_geometrique.py) et modifiez les valeurs de `ParametresBras` (`L1`, `L2`, `a`, `h0` et les butées de fins de course) avec vos mesures SolidWorks exactes.
2. Relancez la vérification et régénérez les figures :
   ```powershell
   python verification_simulation.py
   ```
3. Lancez le simulateur interactif :
   ```powershell
   python simulateur_interactif.py
   ```
