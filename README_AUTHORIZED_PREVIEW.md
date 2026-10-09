# PaceFlow → Python Garmin : étape sécurisée (aperçu uniquement)

Ce lot ajoute `POST /workouts/authorized-preview`. Il lit la séance canonique depuis Supabase après vérification de la session et de la relation athlète/coach, puis convertit son contenu au format Garmin. **Aucun appel Garmin et aucun envoi réel.** Les routes existantes sont conservées.

## Configuration Render (serveur uniquement)

- `SUPABASE_URL` : URL HTTPS du projet Supabase
- `SUPABASE_ANON_KEY` : clé publique Supabase
- `SUPABASE_SERVICE_ROLE_KEY` : clé secrète Supabase, **uniquement dans Render** (jamais GitHub, Netlify frontend, navigateur ou captures)

La clé service-role permet de lire les relations ; les droits sont vérifiés explicitement à partir du JWT utilisateur validé via `/auth/v1/user`. Une séance n'est renvoyée que pour son athlète et un utilisateur lié directement ou par son coach assigné. Les comptes administrateurs ne bénéficient pas d'une exception implicite.

## Requête

`POST /workouts/authorized-preview`

En-tête : `Authorization: Bearer <session Supabase utilisateur>`

Corps : `{"workout_id":"<uuid>","athlete_id":"<uuid>"}`

Réponse : `status=preview`, `garmin_sent=false`, `scheduled_date` provenant de la base et `garmin_workout` converti. En cas d'erreur d'authentification : 401/403. Pas d'identifiants Garmin requis.

## Vérifications

`python -m unittest discover -q`

## Avant la suite

- Tester avec un athlète réel et un coach assigné en environnement de test.
- Vérifier les tables et les règles d'autorisation Supabase réellement déployées.
- Ne pas exposer de route Garmin réelle avant d'avoir conçu des sessions Garmin chiffrées, MFA, consentement explicite, idempotence et audit.
- Les routes `/workouts/convert` et `/workouts/simulate-send` restent publiques dans cette version : elles ne déclenchent aucun envoi mais doivent être restreintes avant production si nécessaire.
