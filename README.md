# EEUEZ Hackathon Teams

Petite app Django pour charger un Excel de participants, prévisualiser, envoyer les emails selon la langue, former des équipes (10 max, 5 pers chacune avec un dev, un marketeur, FR/EN si dispo, leader = niveau académique le plus élevé), nommer les équipes, assigner un encadrant, et générer un Excel final avec onglet General + onglets TEAM 1-10 (scores ateliers inclus).

## Démarrage rapide
1) Créez/activez l'env: `python -m venv .venv` puis `.\.venv\Scripts\activate`
2) Installez: `pip install -r requirements.txt`
3) Appliquez les migrations: `python manage.py migrate`
4) Configurez l'email (voir plus bas) ou laissez en console pour tester.
5) Lancez: `python manage.py runserver` puis ouvrez http://127.0.0.1:8000

## Fonctionnalités
- Upload Excel (.xlsx/.xls), aperçu (50 lignes max), nettoyage des colonnes inutiles.
- Envoi d'emails avec contenu FR/EN/Les deux selon `LANGUE`, suivi des statuts.
- Formation automatique des équipes + export Excel avec équipes/ateliers.
- Nommer une équipe, voir les compétences, assigner un encadrant par équipe.
- Téléchargement de l'Excel final.

## Format attendu du fichier Excel (feuille 1)
Colonnes utilisées: `NOM ET PRENOM`, `Email Address`, `LANGUE`, `NIVEAU D'ETUDES`, `VOS COMPETENCES`.

## Configuration SMTP
Par défaut, le backend SMTP est configuré dans `hackathon_site/settings.py`:
```

```
Vous pouvez surcharger via variables d'env si besoin (voir les clés dans `settings.py`). Assurez-vous que le port 465/SSL est accessible.

## Commandes utiles
- Vérifier l'état Django: `python manage.py check`
- Reset de la base locale (déjà sqlite): supprimer `db.sqlite3` puis `python manage.py migrate`
- Lancement serveur: `python manage.py runserver`

## Structure
- `participants/` : vues, utilitaires d'import/assignation, modèles `Team`/`Participant`, URLs.
- `templates/` : base et dashboard (upload, données traitées, équipes, encadrants).
- `requirements.txt` : dépendances (Django, pandas, openpyxl, numpy).
