# PaceFlow — phase 9 : vérification de l'export des jetons

Cette livraison **n'intègre pas encore les sessions dans api.py**. Elle ajoute un workflow GitHub Actions indépendant pour confirmer la présence et la signature de `client.dumps()` sur `garminconnect==0.3.19`.

## Installation depuis l'iPhone

Sur la branche `feature/garmin-session-persistence` du dépôt `paceflow-garmin-python-test`, ajouter :

- `check_garmin_export_contract.py` à la racine ;
- `.github/workflows/garmin-export-contract.yml` en respectant les sous-dossiers.

Ne pas remplacer `api.py`, ne pas fusionner sur `main`, ne pas déployer Render.

Dans GitHub > Actions > **Garmin export contract (offline)** > Run workflow, sélectionner la branche `feature/garmin-session-persistence`. Le workflow peut ne pas apparaître immédiatement si GitHub ne répertorie pas les nouveaux workflows uniquement présents sur une branche non par défaut ; dans ce cas, l'exécution `push` du workflow sur la branche ou une commande locale équivalente peut être utilisée, sans fusionner `main`.

Le diagnostic n'effectue aucune connexion Garmin et ne manipule aucun jeton réel. Transmettre le journal du job `Inspect token export without credentials` pour valider la suite.

**Note :** la présence de `dumps()` ne prouve pas encore une restauration réussie en production. La persistance Supabase, l'expiration, le MFA et les tests d'envoi devront être validés séparément.
