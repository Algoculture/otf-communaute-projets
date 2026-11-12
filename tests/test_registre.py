import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from registre import calculer_statut, valider  # noqa: E402

AUJ = dt.date(2026, 11, 12)
BASE = {"nom": "X", "objet": "o", "personnes": [{"pseudo": "p"}], "depot": "a/b", "etape": "idee",
        "avancement": "ok", "mis_a_jour": "2026-11-01"}


def st(data, commit=None, **kw):
    return calculer_statut({**BASE, **data}, AUJ, commit)["statut"]


def test_actif():
    assert st({}, (AUJ - dt.timedelta(days=5), False, None)) == "actif"

def test_en_pause():
    assert st({}, (AUJ - dt.timedelta(days=60), False, None)) == "en_pause"

def test_abandonne_probable():
    assert st({}, (AUJ - dt.timedelta(days=120), False, None)) == "abandonne_probable"

def test_depot_archive():
    assert st({}, (AUJ - dt.timedelta(days=2), True, None)) == "abandonne_probable"

def test_depot_introuvable():
    assert st({}, (None, False, "erreur GitHub 404")) == "inconnu"

def test_prive_a_jour():
    assert st({"depot": "prive", "mis_a_jour": "2026-11-01"}) == "actif"

def test_prive_en_pause():
    assert st({"depot": "prive", "mis_a_jour": "2026-08-01"}) == "en_pause"

def test_prive_perime():
    assert st({"depot": "prive", "mis_a_jour": "2026-01-01"}) == "fiche_perimee"

def test_statut_force():
    assert st({"statut_force": "en_pause"}, (AUJ, False, None)) == "en_pause"

def test_statut_force_expire():
    assert st({"statut_force": "en_pause", "statut_force_jusqua": "2026-10-01"}, (AUJ, False, None)) == "actif"


def test_fiche_valide():
    assert valider(Path("x.yml"), dict(BASE)) == []

def test_champ_manquant():
    d = dict(BASE); del d["nom"]
    assert any("nom" in e for e in valider(Path("x.yml"), d))

def test_adresse_mail_refusee():
    d = dict(BASE, avancement="écrivez à quelquun@exemple.org")
    assert any("électronique" in e for e in valider(Path("x.yml"), d))

def test_etape_inconnue():
    assert any("etape" in e for e in valider(Path("x.yml"), dict(BASE, etape="bof")))

def test_depot_invalide():
    assert any("depot" in e for e in valider(Path("x.yml"), dict(BASE, depot="n'importe quoi")))
