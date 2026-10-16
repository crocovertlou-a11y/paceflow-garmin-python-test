# V3.2 — Protection des envois Garmin lors des refus 429

- Le chemin `/workouts/send` utilise désormais le même cooldown mémoire (15 min) que `/activities/candidates`.
- Le contrôle de cooldown se fait AVANT toute revendication d'envoi dans le registre Supabase : aucune séance n'est bloquée par une requête refusée localement.
- Si Garmin retourne un refus 429 à la connexion, le serveur conserve le statut `auth_failed`, active le cooldown, retourne HTTP 429 avec `Retry-After`.
- Une erreur de connexion non classifiée retourne HTTP 503 (et non un diagnostic erroné de mot de passe).
- Aucun changement de la conversion, de l'upload ou de la planification Garmin (`garmin_sender.py` inchangé), ni des fonctions Supabase.

Limites : le cooldown est local au processus Render et est perdu après redémarrage. La bibliothèque garminconnect peut faire plusieurs requêtes ou essais internes avant de lever son exception : ce correctif ne garantit pas l'arrêt à la première réponse HTTP 429 à l'intérieur de cette bibliothèque. Un refus Garmin/Cloudflare ne peut pas être contourné par ce correctif. Ne pas réinitialiser manuellement les envois en échec sans réconciliation.

Vérification hors ligne : `python -m unittest discover -q` (32 tests réussis). Aucun test réel Garmin ni test de bout en bout Netlify/Render.
