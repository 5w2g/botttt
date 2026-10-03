# Bot Rôle Perso Discord

Bot Discord qui permet aux **boosters** du serveur de créer **un rôle unique** entièrement personnalisable (nom, couleur, icône) directement depuis Discord via une interface à boutons + modale. Le rôle est automatiquement attribué au créateur et modifiable à volonté.

## Fonctionnalités

- 🎨 **Création** : les boosters peuvent créer 1 rôle personnalisé
- ✏️ **Modification** : modifiable à l'infini (nom, couleur, icône) via `/perso`
- 🗑️ **Suppression** : bouton dédié pour supprimer son rôle
- 🚀 **Auto-détection** : un MP est envoyé automatiquement quand quelqu'un boost le serveur
- 🖼️ **Icône de rôle** : support des icônes (nécessite serveur niveau 2+)
- 💾 **Persistance** : les rôles sont sauvegardés dans `data/roles.json`

## Installation

### 1. Pré-requis
- **Python 3.10+** ([télécharger](https://www.python.org/downloads/))
- Un compte Discord avec un serveur où tu es admin

### 2. Créer l'application Discord
1. Va sur https://discord.com/developers/applications
2. **New Application** → donne un nom → crée
4. Ong栏 **"Bot"** :
   - **Reset Token** → copie le token (tu ne le reverras plus)
   - Active **SERVER MEMBERS INTENT** et **MESSAGE CONTENT INTENT** (privileged intents)
6. Ong栏 **"OAuth2 → URL Generator"** :
   - Scopes : coche `bot` ET `applications.commands`
   - Permissions : coche **Manage Roles** (et éventuellement Send Messages)
   - Copie l'URL générée en bas, ouvre-la, ajoute le bot à ton serveur

### 3. Configuration
Ouvre un terminal dans le dossier du bot et exécute :

```bash
# Copier le fichier de config
copy .env.example .env
```

Puis édite `.env` avec un éditeur de texte et colle ton token :
```
DISCORD_TOKEN=ton_token_ici
```

### 4. Installer les dépendances
```bash
py -m pip install -r requirements.txt
```
(si `py` ne fonctionne pas, essaie `python -m pip install -r requirements.txt`)

### 5. Lancer le bot
```bash
py bot.py
```

Tu devrais voir :
```
==================================================
  Connecte : TonBot#1234 (123456789012345678)
  1 commande(s) synchronisee(s)
  1 serveur(s) connecte(s)
==================================================
```

### 6. ⚠️ Important : hiérarchie des rôles
Dans **Paramètres du serveur → Rôles**, fais-dragging bien le rôle du bot **au-dessus** de tous les autres rôles (sauf ceux que tu veux absolument garder plus haut). Sans ça, le bot ne pourra pas gérer les rôles qu'il crée.

## Utilisation

- **Slash command** : `/perso` → ouvre l'interface
- **Boutons** :
  - `🎨 Créer / Modifier mon rôle` → ouvre la modale (nom, couleur, URL icône)
  - `🗑️ Supprimer mon rôle` → supprime ton rôle perso
- **Auto** : quand quelqu'un boost, il reçoit un MP avec un bouton direct

### Aide sur les couleurs
Codes hex sans le `#`. Exemples :
- `FF0000` = rouge
- `00FF00` = vert
- `0000FF` = bleu
- `FF5733` = orange
- `9B59B6` = violet

### Aide sur les icônes
- Le serveur doit être **niveau 2** de boost minimum
- L'URL doit pointer directement vers une image (`.png`, `.jpeg`, `.webp`, `.gif` animé supporté)
- Taille max : 256 Ko
- Exemple d'URL valide : `https://i.imgur.com/abc123.png`

## Fichiers

- `bot.py` : code du bot
- `data/roles.json` : sauvegarde des rôles (auto-créé)
- `.env` : token (à créer depuis `.env.example`)
- `requirements.txt` : dépendances Python

## Commandes admin (optionnel)

Tu peux ajouter toi-même :
- `@bot.tree.command(name="resetall")` pour réinitialiser tous les rôles persos
- `@bot.tree.command(name="perso-of", app_commands.describe(user="...")` pour voir le rôle perso d'un membre

## Limitations

- **1 rôle par personne** par serveur (volontaire, c'est le concept)
- Le rôle est créé sans permissions particulières (juste cosmétique)
- Si quelqu'un débosste, son rôle reste (il peut toujours le modifier via /perso)

## Besoin d'aide ?

Erreurs courantes :
- **`Missing Permissions`** → vérifie que le rôle du bot est en haut de la hiérarchie
- **`Missing Intents`** → active "Server Members Intent" dans le Developer Portal
- **Icône ne s'affiche pas** → le serveur doit être niveau 2 de boost