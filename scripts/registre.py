"""Fonctions communes : lecture, validation et calcul d'activité des fiches."""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import yaml

# Seuils réglables (en jours)
SEUIL_ACTIF = 30
SEUIL_PAUSE = 90
SEUIL_DECLARE_ACTIF = 60
SEUIL_DECLARE_PAUSE = 120
SEUIL_FICHE_A_RELIRE = 90

ETAPES = ("idee", "prototype", "utilisable", "production")
STATUTS_FORCES = ("actif", "en_pause", "abandonne")
RE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RE_DEPOT = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RE_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
MAX = {"nom": 80, "objet": 140, "avancement": 200}
PROJETS = Path(__file__).resolve().parent.parent / "projets"


def charger_fiches(dossier: Path = PROJETS):
    fiches = []
    for chemin in sorted(dossier.glob("*.yml")):
        if chemin.name.startswith("_"):
            continue
        with open(chemin, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fiches.append((chemin, data))
    return fiches


def _textes(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _textes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _textes(v)


def _date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v)
        except ValueError:
            return None
    return None


def valider(chemin: Path, data) -> list[str]:
    """Renvoie la liste des erreurs (en français) pour une fiche."""
    e: list[str] = []
    n = chemin.name
    if not RE_ID.match(chemin.stem):
        e.append(f"{n} : nom de fichier invalide (minuscules, chiffres et tirets).")
    if not isinstance(data, dict):
        return e + [f"{n} : la fiche est vide ou mal formée."]
    for champ in ("nom", "objet", "personnes", "depot", "etape", "avancement", "mis_a_jour"):
        if data.get(champ) in (None, "", []):
            e.append(f"{n} : champ obligatoire manquant : {champ}.")
    for champ, maxi in MAX.items():
        v = data.get(champ)
        if isinstance(v, str) and len(v) > maxi:
            e.append(f"{n} : {champ} dépasse {maxi} caractères ({len(v)}).")
    if data.get("etape") and data["etape"] not in ETAPES:
        e.append(f"{n} : etape inconnue « {data['etape']} » (choisir parmi {', '.join(ETAPES)}).")
    depot = data.get("depot")
    if depot and depot not in ("prive", "aucun") and not RE_DEPOT.match(str(depot)):
        e.append(f"{n} : depot doit être « proprietaire/depot », « prive » ou « aucun ».")
    pers = data.get("personnes")
    if pers is not None:
        if not isinstance(pers, list) or not all(isinstance(p, dict) and p.get("pseudo") for p in pers):
            e.append(f"{n} : personnes doit être une liste d'éléments avec au moins un « pseudo ».")
    if data.get("mis_a_jour") and _date(data["mis_a_jour"]) is None:
        e.append(f"{n} : mis_a_jour n'est pas une date AAAA-MM-JJ.")
    sf = data.get("statut_force")
    if sf and sf not in STATUTS_FORCES:
        e.append(f"{n} : statut_force inconnu « {sf} » (actif, en_pause ou abandonne).")
    if data.get("statut_force_jusqua") and _date(data["statut_force_jusqua"]) is None:
        e.append(f"{n} : statut_force_jusqua n'est pas une date AAAA-MM-JJ.")
    if any(RE_MAIL.search(t) for t in _textes(data)):
        e.append(f"{n} : une adresse électronique a été trouvée ; elle est interdite, merci de la retirer.")
    return e


def dernier_commit(depot: str, jeton: str | None = None):
    """Renvoie (date, archive, erreur). Un seul appel, tolérant aux erreurs."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "otf-registre"}
    if jeton:
        headers["Authorization"] = f"Bearer {jeton}"

    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.load(r)

    try:
        info = get(f"https://api.github.com/repos/{depot}")
        commits = get(f"https://api.github.com/repos/{depot}/commits?per_page=1")
        quand = commits[0]["commit"]["committer"]["date"]
        return dt.datetime.fromisoformat(quand.replace("Z", "+00:00")).date(), bool(info.get("archived")), None
    except urllib.error.HTTPError as ex:
        return None, False, f"erreur GitHub {ex.code}"
    except Exception as ex:  # réseau, JSON, dépôt vide...
        return None, False, f"lecture impossible ({type(ex).__name__})"


def calculer_statut(data: dict, aujourdhui: dt.date, commit=None):
    """commit = (date|None, archive, erreur) pour un dépôt public, sinon None.
    Renvoie un dict : statut, declare, jours, commit_date, raison."""
    force = data.get("statut_force")
    fin = _date(data.get("statut_force_jusqua"))
    if force and (fin is None or fin >= aujourdhui):
        s = {"abandonne": "abandonne_probable"}.get(force, force)
        return {"statut": s, "declare": True, "jours": None, "commit_date": None, "raison": "statut déclaré"}
    depot = data.get("depot")
    if depot not in ("prive", "aucun") and commit is not None:
        date, archive, err = commit
        if err or date is None:
            return {"statut": "inconnu", "declare": False, "jours": None, "commit_date": None, "raison": err or "pas de commit"}
        jours = (aujourdhui - date).days
        if archive:
            statut = "abandonne_probable"
        elif jours < SEUIL_ACTIF:
            statut = "actif"
        elif jours <= SEUIL_PAUSE:
            statut = "en_pause"
        else:
            statut = "abandonne_probable"
        return {"statut": statut, "declare": False, "jours": jours, "commit_date": date.isoformat(),
                "raison": "dépôt archivé" if archive else f"sans commit depuis {jours} jours"}
    maj = _date(data.get("mis_a_jour"))
    if maj is None:
        return {"statut": "inconnu", "declare": True, "jours": None, "commit_date": None, "raison": "date de fiche absente"}
    jours = (aujourdhui - maj).days
    if jours < SEUIL_DECLARE_ACTIF:
        statut = "actif"
    elif jours <= SEUIL_DECLARE_PAUSE:
        statut = "en_pause"
    else:
        statut = "fiche_perimee"
    return {"statut": statut, "declare": True, "jours": jours, "commit_date": None,
            "raison": f"fiche relue il y a {jours} jours (non vérifiable)"}


def fiche_a_relire(data: dict, aujourdhui: dt.date) -> bool:
    maj = _date(data.get("mis_a_jour"))
    return maj is not None and (aujourdhui - maj).days > SEUIL_FICHE_A_RELIRE
