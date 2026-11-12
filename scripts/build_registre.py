"""Calcule l'activité de chaque projet et génère README (tableau), docs/index.html et docs/registre.json.
Usage : python scripts/build_registre.py [--offline] [--aujourdhui AAAA-MM-JJ]"""
import argparse
import datetime as dt
import html
import json
import os
import time
from collections import defaultdict
from pathlib import Path

from registre import calculer_statut, charger_fiches, dernier_commit, fiche_a_relire

RACINE = Path(__file__).resolve().parent.parent
DEBUT, FIN = "<!-- REGISTRE:DEBUT -->", "<!-- REGISTRE:FIN -->"
PASTILLE = {"actif": "🟢", "en_pause": "🟡", "abandonne_probable": "🔴", "fiche_perimee": "🔴", "inconnu": "⚪"}
LIBELLE = {"actif": "actif", "en_pause": "en pause", "abandonne_probable": "sans activité",
           "fiche_perimee": "fiche périmée", "inconnu": "inconnu"}


def construire(aujourdhui, offline):
    jeton = os.environ.get("GITHUB_TOKEN")
    lignes = []
    for chemin, data in charger_fiches():
        commit = None
        depot = data.get("depot")
        if not offline and depot not in ("prive", "aucun"):
            commit = dernier_commit(depot, jeton)
            time.sleep(0.3)  # moins de 4 appels par seconde
        st = calculer_statut(data, aujourdhui, commit)
        lignes.append({
            "id": chemin.stem, "nom": data["nom"], "objet": data["objet"],
            "personnes": [p["pseudo"] for p in data["personnes"]],
            "depot": depot, "lien": data.get("lien"), "etape": data["etape"],
            "avancement": data["avancement"], "fonctions": data.get("fonctions") or [],
            "mis_a_jour": str(data["mis_a_jour"]), "a_relire": fiche_a_relire(data, aujourdhui), **st,
        })
    return lignes


def tableau_md(lignes):
    out = ["| Projet | Personnes | Activité | Étape | Avancement | Fonctions |", "|---|---|---|---|---|---|"]
    for l in lignes:
        nom = f"[{l['nom']}](https://github.com/{l['depot']})" if "/" in str(l["depot"]) else l["nom"]
        act = f"{PASTILLE[l['statut']]} {LIBELLE[l['statut']]}" + (" (déclaré)" if l["declare"] else "")
        act += f"<br><sub>{l['raison']}</sub>"
        if l["a_relire"]:
            act += "<br><sub>⚠️ fiche à relire</sub>"
        out.append(f"| {nom} | {', '.join(l['personnes'])} | {act} | {l['etape']} | {l['avancement']} | {', '.join(l['fonctions'])} |")
    return "\n".join(out)


def doublons(lignes):
    par = defaultdict(list)
    for l in lignes:
        for f in l["fonctions"]:
            par[f.strip().lower()].append(l["nom"])
    return {f: n for f, n in sorted(par.items()) if len(n) > 1}


def doublons_md(lignes):
    d = doublons(lignes)
    if not d:
        return "_Aucune fonction partagée pour l'instant._"
    return "\n".join(f"- **{f}** : {', '.join(n)}" for f, n in d.items())


def page_html(lignes, aujourdhui):
    e = html.escape
    rows = ""
    for l in lignes:
        nom = e(l["nom"])
        if "/" in str(l["depot"]):
            nom = f'<a href="https://github.com/{e(l["depot"])}">{nom}</a>'
        rows += (f"<tr><td>{nom}<br><small>{e(l['objet'])}</small></td><td>{e(', '.join(l['personnes']))}</td>"
                 f"<td data-v='{e(l['statut'])}'>{PASTILLE[l['statut']]} {e(LIBELLE[l['statut']])}"
                 f"{' (déclaré)' if l['declare'] else ''}<br><small>{e(l['raison'])}</small></td>"
                 f"<td>{e(l['etape'])}</td><td>{e(l['avancement'])}</td><td>{e(', '.join(l['fonctions']))}</td></tr>")
    dbl = "".join(f"<li><b>{e(f)}</b> : {e(', '.join(n))}</li>" for f, n in doublons(lignes).items()) or "<li>Aucune fonction partagée pour l'instant.</li>"
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Projets de la communauté OTF</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}}
.t{{overflow-x:auto}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}}
th{{cursor:pointer;background:#f3f3f3}}small{{color:#666}}input{{padding:6px;margin:8px 0;width:100%;max-width:320px}}</style></head><body>
<h1>Projets de la communauté Ouvre ta ferme</h1><p>Mis à jour le {aujourdhui.strftime('%d/%m/%Y')}. Cliquez sur une colonne pour trier.</p>
<input id="f" placeholder="Filtrer (fonction, personne...)" oninput="filtre()">
<div class="t"><table id="t"><thead><tr><th>Projet</th><th>Personnes</th><th>Activité</th><th>Étape</th><th>Avancement</th><th>Fonctions</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Fonctions suivies par plusieurs projets</h2><ul>{dbl}</ul>
<script>
function filtre(){{var q=document.getElementById('f').value.toLowerCase();document.querySelectorAll('#t tbody tr').forEach(function(r){{r.style.display=r.textContent.toLowerCase().indexOf(q)<0?'none':''}})}}
document.querySelectorAll('#t th').forEach(function(h,i){{h.onclick=function(){{var b=document.querySelector('#t tbody'),r=Array.from(b.rows);r.sort(function(x,y){{return x.cells[i].textContent.localeCompare(y.cells[i].textContent,'fr')}});r.forEach(function(x){{b.appendChild(x)}})}}}});
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--aujourdhui")
    a = ap.parse_args()
    auj = dt.date.fromisoformat(a.aujourdhui) if a.aujourdhui else dt.date.today()
    lignes = construire(auj, a.offline)
    (RACINE / "docs").mkdir(exist_ok=True)
    (RACINE / "docs" / "registre.json").write_text(json.dumps({"genere_le": auj.isoformat(), "projets": lignes}, ensure_ascii=False, indent=2), encoding="utf-8")
    (RACINE / "docs" / "index.html").write_text(page_html(lignes, auj), encoding="utf-8")
    readme = RACINE / "README.md"
    txt = readme.read_text(encoding="utf-8")
    bloc = f"{DEBUT}\n_Mis à jour le {auj.strftime('%d/%m/%Y')}._\n\n{tableau_md(lignes)}\n\n### Fonctions suivies par plusieurs projets\n\n{doublons_md(lignes)}\n{FIN}"
    if DEBUT in txt and FIN in txt:
        txt = txt[:txt.index(DEBUT)] + bloc + txt[txt.index(FIN) + len(FIN):]
        readme.write_text(txt, encoding="utf-8")
    print(f"{len(lignes)} projet(s) traité(s).")


if __name__ == "__main__":
    main()
