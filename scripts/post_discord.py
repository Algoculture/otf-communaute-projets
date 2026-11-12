"""Envoie le résumé hebdomadaire sur Discord. Le webhook vient de DISCORD_WEBHOOK_URL (secret).
Usage : python scripts/post_discord.py [--dry-run]"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from build_registre import doublons

RACINE = Path(__file__).resolve().parent.parent


def message(donnees, url_page):
    p = donnees["projets"]
    n = lambda s: sum(1 for x in p if x["statut"] == s)
    sans = n("abandonne_probable") + n("fiche_perimee")
    lignes = [f"📋 Registre des projets OTF · {donnees['genere_le']}",
              f"{len(p)} projets : {n('actif')} actifs 🟢 · {n('en_pause')} en pause 🟡 · {sans} sans activité 🔴 · {n('inconnu')} inconnus ⚪"]
    d = doublons(p)
    if d:
        lignes.append("Fonctions suivies par plusieurs projets : " + ", ".join(f"{f} ({len(v)})" for f, v in d.items()))
    rel = [x for x in p if x["a_relire"]]
    if rel:
        lignes.append("Fiches à relire : " + ", ".join(x["nom"] for x in rel))
    if url_page:
        lignes.append(f"Détail : {url_page}")
    return "\n".join(lignes)[:1800]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    donnees = json.loads((RACINE / "docs" / "registre.json").read_text(encoding="utf-8"))
    texte = message(donnees, os.environ.get("URL_PAGE", ""))
    if a.dry_run:
        print(texte)
        return 0
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        print("Discord non configuré : rien envoyé.")
        return 0
    corps = json.dumps({"content": texte, "allowed_mentions": {"parse": []}}).encode()
    req = urllib.request.Request(url, corps, {"Content-Type": "application/json", "User-Agent": "otf-registre"})
    urllib.request.urlopen(req, timeout=20).read()
    print("Résumé envoyé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
