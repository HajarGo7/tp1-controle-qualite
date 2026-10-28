"""Contrôle qualité d'une ligne d'usinage : lecture des mesures, verdicts, statistiques, rapport."""
import math

NOMINAL = 25.0     # diamètre nominal des axes, en mm
TOLERANCE = 0.05   # tolérance admise : 25,00 ± 0,05 mm


# --- Étape 1 : lire les données -----------------------------------------------------------------
def lire_mesure(texte: str) -> float:
    """Convertit une mesure saisie par le palpeur en nombre."""

    # 1. Nettoyer et préparer le texte
    mesure_texte = texte.strip().lower()
    mesure_texte = mesure_texte.removesuffix("mm")
    mesure_texte = mesure_texte.strip()
    mesure_texte = mesure_texte.replace(",", ".")

    # 2. Convertir en float
    try:
        mesure = float(mesure_texte)
    except ValueError:
        raise ValueError(f"mesure invalide : {texte.strip()!r}")

    # 3. Refuser les valeurs non positives ou non finies
    if mesure <= 0 or not math.isfinite(mesure):
        raise ValueError(f"mesure invalide : {texte.strip()!r}")

    return mesure
    


def valider_code(code: str) -> bool:
    """Vrai si le code pièce respecte le format AAA-9999."""  

    return (
        len(code) == 8
        and code[:3].isalpha()
        and code[:3].isupper()
        and code[:3].isascii()
        and code[3] == "-"
        and code[4:].isdigit()
        and code[4:].isascii()
    )


# --- Étape 2 : décider ----------------------------------------------------------------------------
def ecart(mesure: float, nominal: float = NOMINAL) -> float:
    """Écart à la cote nominale, arrondi à 3 décimales."""
    return round(mesure - nominal, 3)


def verdict(mesure: float, nominal: float = NOMINAL,
            tolerance: float = TOLERANCE) -> str:
    """Renvoie conforme, à reprendre ou rebut."""

    if tolerance <= 0:
        raise ValueError("La tolérance doit être strictement positive")

    difference = ecart(mesure, nominal)

    if abs(difference) <= tolerance:
        return "conforme"
    elif difference > tolerance:
        return "à reprendre"
    else:
        return "rebut"


# --- Étape 3 : analyser une ligne -----------------------------------------------------------------
def analyser_ligne(ligne: str, *, nominal: float = NOMINAL, tolerance: float = TOLERANCE) -> tuple[str, float, str]:
    """Analyse une ligne "AXE-0042 ; 25,03 mm" et renvoie (code, mesure, verdict).

    Lève ValueError si la ligne n'a pas deux champs, si le code ou la mesure est invalide.
    """
    morceaux = ligne.split(";")

    if len(morceaux) != 2:
        raise ValueError(f"2 champs attendus, {len(morceaux)} trouvé(s)")

    code = morceaux[0].strip().upper()

    if not valider_code(code):
        raise ValueError(f"code invalide : {code!r}")

    mesure = lire_mesure(morceaux[1])

    resultat = verdict(mesure, nominal=nominal, tolerance=tolerance)

    return (code, mesure, resultat)


# --- Étape 4 : analyser un lot --------------------------------------------------------------------

def analyser_lot(
    lignes: list[str],
    **reglages
) -> tuple[list[tuple[str, float, str]], list[str]]:
    """Analyse toutes les lignes d'un lot et renvoie (resultats, erreurs)."""

    resultats = []
    erreurs = []

    for numero, ligne in enumerate(lignes, start=1):

        # Ignorer les lignes vides et les commentaires
        if not ligne.strip() or ligne.strip().startswith("#"):
            continue

        # Analyser chaque ligne sans arrêter le lot en cas d'erreur
        try:
            resultat = analyser_ligne(ligne, **reglages)
            resultats.append(resultat)

        except ValueError as err:
            erreurs.append(f"ligne {numero} : {err}")

    return resultats, erreurs




def compter_verdicts(
    resultats: list[tuple[str, float, str]]
) -> tuple[int, int, int]:
    """Renvoie le nombre de pièces conformes, à reprendre et rebuts."""

    conformes = 0
    a_reprendre = 0
    rebuts = 0

    for code, mesure, v in resultats:
        if v == "conforme":
            conformes += 1
        elif v == "à reprendre":
            a_reprendre += 1
        elif v == "rebut":
            rebuts += 1

    return conformes, a_reprendre, rebuts



# --- Étape 5 : statistiques et capabilité ---------------------------------------------------------

def moyenne(*valeurs: float) -> float:
    """Moyenne d'un nombre quelconque de valeurs."""

    if len(valeurs) == 0:
        raise ValueError("aucune valeur")

    somme = 0
    for valeur in valeurs:
        somme += valeur

    return somme / len(valeurs)


def ecart_type(*valeurs: float) -> float:
    """Écart type d'échantillon (division par n - 1)."""

    if len(valeurs) < 2:
        raise ValueError("au moins deux valeurs sont nécessaires")

    m = moyenne(*valeurs)

    somme_carres = 0
    for valeur in valeurs:
        somme_carres += (valeur - m) ** 2

    return math.sqrt(somme_carres / (len(valeurs) - 1))


def capabilite(
    mesures: list[float],
    *,
    nominal: float = NOMINAL,
    tolerance: float = TOLERANCE
) -> tuple[float, float]:
    """Calcule les indices Cp et Cpk, arrondis à 2 décimales."""

    if tolerance <= 0:
        raise ValueError("la tolérance doit être strictement positive")

    s = ecart_type(*mesures)

    if s == 0:
        raise ValueError("écart type nul")

    m = moyenne(*mesures)

    Tmin = nominal - tolerance
    Tmax = nominal + tolerance

    cp = (Tmax - Tmin) / (6 * s)
    cpk = min(Tmax - m, m - Tmin) / (3 * s)

    return round(cp, 2), round(cpk, 2)



# --- Étape 6 : le rapport -------------------------------------------------------------------------


def rapport(
    lignes: list[str],
    *,
    nominal: float = NOMINAL,
    tolerance: float = TOLERANCE
) -> str:
    """Construit le rapport de contrôle d'un lot."""

    resultats, erreurs = analyser_lot(
        lignes, nominal=nominal, tolerance=tolerance
    )

    sortie = [
    f"Contrôle des axes : {nominal:.2f} ± {tolerance:.2f} mm",
    "Code        Mesure    Écart   Verdict"
    ]
    mesures = []

    for code, mesure, v in resultats:
        e = ecart(mesure, nominal)
        sortie.append(
            f"{code:<10} {mesure:>7.3f}   {e:+.3f}   {v}"
        )
        mesures.append(mesure)

    conformes, a_reprendre, rebuts = compter_verdicts(resultats)
    total = len(resultats)

    pourcentage = 100 * conformes / total if total else 0.0

    sortie.extend([
        "",
        f"Pièces : {total} | conformes : {conformes} "
        f"({pourcentage:.1f}%) | à reprendre : {a_reprendre} "
        f"| rebuts : {rebuts}"
    ])

    if len(mesures) >= 2:
        cp, cpk = capabilite(
            mesures, nominal=nominal, tolerance=tolerance
        )
        conclusion = (
            "procédé capable" if cpk >= 1.33
            else "procédé NON capable"
        )
        sortie.append(
    f"Cp = {cp:.2f} | Cpk = {cpk:.2f} -> {conclusion}"
       )
    if erreurs:
        sortie.append(f"Lignes rejetées : {len(erreurs)}")
        sortie.extend(f"  {erreur}" for erreur in erreurs)

    return "\n".join(sortie)


# --- Étape 7 : le rapport -------------------------------------------------------------------------


def executer(commande: str, saisies: list) -> bool:
    """Exécute une commande et renvoie False pour quitter."""

    morceaux = commande.split()

    match morceaux:
        case ["mesure", code, valeur]:
            try:
                resultat = analyser_ligne(f"{code};{valeur}")
            except ValueError as err:
                print(f"Refusé : {err}")
            else:
                code, mesure, v = resultat
                saisies.append(resultat)
                print(f"{code} : {mesure:.3f} mm -> {v}")

        case ["mesure", *_]:
            print("Utilisation : mesure CODE VALEUR")

        case ["lot"]:
            print(rapport(LOT_A))

        case ["aide"]:
            print(AIDE)

        case ["quitter"]:
            print(
                f"{len(saisies)} pièce(s) contrôlée(s) à la main. "
                "Au revoir."
            )
            return False

        case _:
            print(f"Commande inconnue : {commande!r} (tapez aide)")

    return True



# --- Étape 8 (à la maison) : histogramme ----------------------------------------------------------


def histogramme(
    mesures: list[float],
    *,
    debut: float,
    pas: float,
    nb_classes: int
) -> str:
    """Construit un histogramme texte des mesures."""

    if pas <= 0:
        raise ValueError("Le pas doit être strictement positif")

    if nb_classes <= 0:
        raise ValueError(
            "Le nombre de classes doit être strictement positif"
        )

    classes = [0] * nb_classes

    for mesure in mesures:
        for i in range(nb_classes):
            borne_inf = debut + i * pas
            borne_sup = debut + (i + 1) * pas

            if borne_inf <= mesure < borne_sup:
                classes[i] += 1
                break

    sortie = []

    for i in range(nb_classes):
        borne_inf = debut + i * pas
        borne_sup = debut + (i + 1) * pas
        etoiles = "*" * classes[i]

        sortie.append(
            f"[{borne_inf:.3f} ; {borne_sup:.3f}[ {etoiles}"
        )

    return "\n".join(sortie)


