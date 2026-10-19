# PaceFlow — session Garmin, validation avant déploiement

Tests locaux effectués : 3 tests simulés de la restauration, de la première connexion et du refus sans reconnexion automatique. Ils ne testent pas la bibliothèque Garmin en réseau.

## Bloquants avant production
1. Vérifier sur une instance de test la signature exacte de `Garmin.login(tokenstore=...)` et la méthode `client.garth.dump(...)` de la version installée.
2. Vérifier que `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GARMIN_SESSION_FERNET_KEY` sont configurés sur Render, et créer la table SQL dans Supabase.
3. Vérifier que `athlete_profiles.id` est bien l'identifiant employé par le registre de transfert.
4. Tester la sauvegarde/restauration avec un compte de test autorisé, sans publier les jetons.
5. Ne pas réenvoyer la séance existante en `auth_failed` sans réconciliation de l'historique Garmin.

Le code ne contourne ni les protections Cloudflare ni les limites Garmin. Il ne prouve pas que l'authentification sera acceptée.
