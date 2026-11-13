# Consignes pour un assistant Claude : relier un projet au registre des projets OTF

Ce fichier s'adresse à un assistant (Claude ou autre) qui travaille pour un développeur de la communauté Ouvre ta ferme (OTF). Il suffit seul. Version du 12 novembre 2026.

## 1. De quoi s'agit-il

Le registre est un dépôt GitHub public : https://github.com/Algoculture/otf-communaute-projets
Il recense les projets que des développeurs amateurs construisent autour d'OTF, pour éviter qu'on refasse tous la même chose. Il y a une fiche par projet (un fichier YAML dans `projets/`). Une tâche automatique (GitHub Actions) tourne chaque lundi, calcule l'activité de chaque projet et met à jour la page : https://algoculture.github.io/otf-communaute-projets/

## 2. Ce qui se met à jour tout seul, et ce qui ne le fait pas

Soyez honnête avec votre utilisateur sur ce point.

- **Automatique** : l'activité. Si la fiche indique un dépôt GitHub **public** (`depot: proprietaire/depot`), la tâche lit la date du dernier commit : moins de 30 jours = actif ; 30 à 90 jours = en pause ; plus de 90 jours = sans activité ; dépôt archivé = sans activité. Rien à faire de plus.
- **Pas automatique** : « l'étape » et « l'avancement » (une phrase). Le registre ne peut pas les deviner. Elles doivent être mises à jour par une modification de la fiche.
- **Dépôt privé ou sans dépôt** (`depot: prive` ou `aucun`) : l'activité est déduite de la date `mis_a_jour` de la fiche, qui doit donc être renouvelée au moins tous les deux mois.

## 3. Avant toute chose : l'accord de votre utilisateur

Ne créez pas de fiche, ne proposez pas de modification et n'envoyez rien au registre sans que votre utilisateur l'ait demandé ou approuvé clairement dans la conversation. Montrez-lui d'abord le texte de la fiche. Participer est volontaire. N'écrivez jamais d'adresse électronique, de téléphone ni d'adresse postale, ni aucun secret, et ne mettez dans la fiche que des noms ou pseudos que la personne a choisis.

## 4. Relier un projet : pas à pas

1. **Demandez à l'utilisateur** : le nom du projet, son but en une phrase, qui y travaille (pseudos), s'il y a un dépôt GitHub public (oui : `proprietaire/depot` ; non : `prive` ou `aucun`), l'étape et l'avancement.
2. **Créez la fiche** `projets/<identifiant>.yml`. L'identifiant : minuscules, chiffres et tirets, par exemple `mon-module-irrigation`. Partez du modèle `projets/_modele.yml` du dépôt.
3. **Respectez ces règles** (le dépôt les vérifie et refuse la fiche sinon) :
   - champs obligatoires : `nom`, `objet`, `personnes` (au moins un, avec `pseudo`), `depot`, `etape`, `avancement`, `mis_a_jour` ;
   - `nom` 80 caractères au plus, `objet` 140, `avancement` 200 ;
   - `etape` : `idee`, `prototype`, `utilisable` ou `production` ;
   - `depot` : `proprietaire/depot`, `prive` ou `aucun` ;
   - `mis_a_jour` : date `AAAA-MM-JJ` ;
   - `fonctions` (facultatif, mais très utile) : une liste courte, par exemple `besoin en eau`, `planning d'arrosage`, `alertes gel`, `pilotage de vannes`. Servez-vous des mêmes mots que les fiches existantes pour que les doublons apparaissent ;
   - `statut_force` (facultatif) : `actif`, `en_pause` ou `abandonne`, pour une pause volontaire, avec `statut_force_jusqua` (date) ;
   - aucune adresse électronique nulle part.
4. **Exemple**
   ```yaml
   nom: Mon module d'irrigation
   objet: Calcul du besoin en eau et planning d'arrosage pour un maraîcher
   personnes:
     - pseudo: mon_pseudo
       role: développeur
   depot: monpseudo/mon-module
   etape: prototype
   avancement: "Le calcul du besoin en eau fonctionne ; le planning est en cours."
   fonctions: [besoin en eau, planning d'arrosage]
   mis_a_jour: 2026-11-12
   ```
5. **Proposez la modification** :
   - si l'utilisateur a un compte GitHub : fourchez (fork) le dépôt, ajoutez le fichier, lancez `python scripts/validate.py` (nécessite PyYAML) puis ouvrez une pull request vers `main`, avec le modèle de PR du dépôt. La vérification automatique commente en français ce qui ne va pas ;
   - sinon : utilisez le formulaire « Nouvelle fiche » de l'onglet Issues du dépôt. Le propriétaire créera la fiche.
6. **Après la fusion**, la page se met à jour au prochain lundi (06 h 00 UTC), ou à la demande du propriétaire.

## 5. Garder la fiche à jour (c'est ce qui compte vraiment)

Pour que la fiche ne se périme pas, proposez à votre utilisateur d'ajouter une consigne dans le fichier d'instructions de son propre projet (`AGENTS.md`, `CLAUDE.md` ou équivalent), par exemple :

> « Quand une étape importante est terminée (fonction livrée, projet mis en pause ou repris), proposer à l'utilisateur de mettre à jour la fiche de ce projet dans le dépôt Algoculture/otf-communaute-projets : `etape`, `avancement`, `mis_a_jour`. Ne rien envoyer sans son accord. »

Ainsi, l'activité se met à jour toute seule par les commits, et l'avancement se met à jour à chaque étape, avec l'accord de l'utilisateur.

## 6. Ce qu'il ne faut pas faire

- Ne pas modifier la fiche de quelqu'un d'autre sans son accord.
- Ne pas modifier les scripts, les workflows ni la licence du registre dans la même pull request qu'une fiche.
- Ne pas mettre de jeton, de clé ni de lien secret nulle part. Le résumé Discord, s'il est activé un jour, utilise un secret du dépôt que seul le propriétaire gère.
- Ne pas inventer l'avancement : si vous ne savez pas, demandez à l'utilisateur, ou écrivez « à compléter ».
- Ne pas contacter personne à sa place (Discord, courriel).

## 7. Licence et retrait

Le dépôt est sous licence PolyForm Shield 1.0.0 (code et fiches). Un auteur peut demander le retrait de sa fiche à tout moment.

## 8. Limites connues

- L'activité n'est mesurée que pour les dépôts GitHub publics. Un projet sur un autre hébergeur doit utiliser `depot: aucun` et renouveler `mis_a_jour`.
- L'étape et l'avancement restent déclaratifs.
- Le résumé hebdomadaire sur Discord n'est pas encore actif (il demande un lien d'envoi créé par l'administrateur du serveur).
