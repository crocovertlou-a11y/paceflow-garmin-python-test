# Garmin Python V3.1 — erreur 429

À déployer **uniquement dans le dépôt GitHub du pont Python** (`paceflow-garmin-python-test`), à la racine, en conservant les dossiers/fichiers du ZIP. Render redéploie ensuite depuis ce dépôt. **Ne pas déployer dans le dépôt PaceFlow Netlify.**

- Endpoint `/activities/candidates` : un refus Garmin 429 devient HTTP 429 explicite avec `Retry-After: 900` (15 minutes indicatives), au lieu d'un succès trompeur.
- Verrou de 15 minutes **local au processus** après un 429 pour limiter les essais supplémentaires sur le même worker. Ce n'est pas un verrou distribué ni une garantie que Garmin débloque après 15 minutes.
- Refus explicite des identifiants : 401. Autres erreurs de connexion : 502. Aucun mot de passe ni code MFA journalisé par notre correctif.
- Envoi Garmin existant, synchronisation Google Sheets, Supabase et interface Netlify **non modifiés**.
- Important : la bibliothèque `garminconnect` peut effectuer ses propres tentatives de connexion avant de retourner 429. Le correctif ne peut pas empêcher ces tentatives internes et ne contourne pas le blocage Garmin.
- Le `504` Netlify peut encore se produire si Render démarre trop lentement : ce correctif ne garantit pas sa suppression.

## Vérification
1. Déployer sur GitHub Python et attendre `Live` sur Render.
2. Vérifier `/health` sans connexion Garmin.
3. Ne **pas** réessayer Garmin immédiatement après les 429 déjà constatés ; laisser le blocage se résorber.
4. Au prochain essai, si Garmin refuse encore, vérifier que les logs montrent `POST /activities/candidates ... 429` et non `200`.

Les tests locaux ne valident pas l'accès réel à Garmin, Render ou Netlify.
