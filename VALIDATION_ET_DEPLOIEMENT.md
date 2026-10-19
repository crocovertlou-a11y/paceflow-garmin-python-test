# PaceFlow — vérification avant déploiement

## Correctif
- Gestion HTTP 429 explicite dans `/workouts/send` après échec d'authentification.
- Restauration/sauvegarde chiffrée par athlète dans `garmin_session_store.py` (fonctionnalité issue de la version précédente).

## Pré-requis obligatoires
1. Exécuter `SQL_GARMIN_SESSIONS.sql` dans Supabase et vérifier que la table existe.
2. Configurer dans Render `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GARMIN_SESSION_FERNET_KEY` (clé Fernet valide et stable).
3. Vérifier la compatibilité de l'API `garminconnect` réellement installée avec `client.login(tokenstore=...)` et `client.garth.dump(...)` avant déploiement.
4. Ne pas changer la clé Fernet après création des sessions, sinon elles deviennent illisibles.
5. Ne pas retenter l'envoi de la séance déjà marquée `auth_failed` sans rapprochement préalable du registre et de Garmin Connect.

## Tests exécutés localement
- `python -m compileall -q .` : OK.
- `python -m unittest test_garmin_session_store -v` : 3/3 OK (simulations).

## Non validé
- API `garminconnect` réelle non installée dans l'environnement de test.
- Connexion Garmin réelle, restauration de jetons réels, envoi de séance et temps de réponse.
- Ce paquet n'est PAS certifié pour un déploiement production sans pré-requis.
