"""Valide toutes les fiches. Sortie 0 si tout est bon, 1 sinon."""
import sys
from collections import Counter

from registre import charger_fiches, valider


def main() -> int:
    erreurs = []
    fiches = charger_fiches()
    for chemin, data in fiches:
        erreurs += valider(chemin, data)
    noms = Counter(str(d.get("nom", "")).strip().lower() for _, d in fiches if isinstance(d, dict))
    erreurs += [f"Deux fiches portent le même nom : « {n} »." for n, c in noms.items() if n and c > 1]
    for err in erreurs:
        print("ERREUR", err)
    print(f"{len(fiches)} fiche(s) lue(s), {len(erreurs)} erreur(s).")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
