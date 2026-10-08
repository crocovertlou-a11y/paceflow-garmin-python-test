# PaceFlow — Garmin Python POC (isolé)

**Prototype expérimental, non officiel, non testé contre un compte Garmin réel.** Ne déployez pas ceci en tant que service public. Ne mettez jamais d'identifiants Garmin dans GitHub, des variables d'environnement publiques ou ChatGPT.

## Sur iPhone avec GitHub Codespaces
1. Créez un dépôt **privé** GitHub contenant uniquement ces 3 fichiers (ne remplacez pas le dépôt PaceFlow).
2. Dans GitHub, ouvrez **Code > Codespaces > Create codespace**. Safari iPhone peut nécessiter « Demander le site pour ordinateur » et un clavier externe peut faciliter le terminal.
3. Dans le terminal Codespaces, exécutez :

```bash
python --version
python -m pip install -r requirements.txt
python main.py
```

L'aperçu affiche le JSON et ne contacte pas Garmin. Contrôlez la structure et l'objectif d'allure avant tout envoi.

4. Si l'aperçu est conforme, pour **un seul test consenti** :

```bash
python main.py --date 2026-10-09 --send
```

Le programme demande une confirmation explicite puis les identifiants **dans le terminal privé**, et un éventuel code MFA. Il n'enregistre pas de jetons sur disque intentionnellement. Vérifiez les réglages de confidentialité et la conservation du terminal Codespaces. Détruisez le Codespace après l'essai.

5. Après confirmation de la présence de la séance dans Garmin Connect, une autre commande optionnelle peut être ajoutée pour pousser sur un appareil. Le flag `--push-device` appelle l'appareil utilisé en dernier et doit être employé uniquement après vérification.

## Limites et avertissements
- **Aucun changement à PaceFlow ni à Nolio.** Ne déployez pas ce dossier sur Netlify.
- La représentation JSON Garmin est une hypothèse de compatibilité à tester : selon la version de la bibliothèque, les identifiants de cibles/allures peuvent être différents. **Ne pas conclure au succès sans vérifier les étapes sur Garmin Connect.**
- 4 récupérations de 60 s, y compris après la quatrième répétition.
- Une séance identique existe déjà via Fitness AI Connector : ce test créera un **doublon** si envoyé à la même date. Pour éviter cela, choisissez une date de test différente ou supprimez d'abord l'ancienne séance.
- Garmin Connect peut refuser l'authentification non officielle, déclencher MFA, ou modifier les API. Une connexion réussie n'autorise pas nécessairement l'usage commercial.
- Un hébergement cloud gratuit n'est pas garanti; Codespaces est soumis aux quotas de votre compte.
