"""Programme principal : un petit terminal de contrôle qualité, piloté par des commandes."""
from donnees import LOT_A
from qualite import analyser_ligne, rapport

AIDE = """Commandes :
  mesure CODE VALEUR   contrôler une pièce (ex. : mesure AXE-0100 25,04)
  lot                  rapport du lot A
  aide                 afficher cette aide
  quitter              terminer"""



def executer(commande: str, saisies: list[str]) -> bool:
    """Exécute une commande ; renvoie False quand il faut quitter."""

    match commande.split():
        case ["mesure", code, valeur]:
            try:
                resultat = analyser_ligne(f"{code};{valeur}")
            except ValueError as erreur:
                print(f"Refusé : {erreur}")
            else:
                code, mesure, verdict = resultat
                saisies.append(resultat)
                print(f"{code} : {mesure:.3f} mm -> {verdict}")

        case ["mesure", *_]:
            print(f"Commande inconnue : {commande!r} (tapez aide)")

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



def main() -> None:
    print("Contrôle qualité, ligne 2. Tapez aide pour la liste des commandes.")
    saisies: list[str] = []
    continuer = True
    while continuer:
        continuer = executer(input("> ").strip(), saisies)


if __name__ == "__main__":
    main()
