# Documentation QGIS Chloe (version plugin 0.9)


## Contexte

Le programme **Chloe QGIS Plugin** permet d'utiliser le programme **Chloe** depuis de QGIS.

Ce plugin contient :
  - Le code Chloe (JAVA), LICENCE CeCill (opensource compatible GPL)
  - Le code du plugin QGIS s'interfacant avec le code Chole (opensource, GPL v3)



## Installation

### Installation via le dépôt INRA

Sous QGIS, effectuer les étapes suivantes:

- *Menu->Extension->Installer/Gérer les extensions
  - *Onglet->Paramètre
    - Activer "Afficher les extensions expérimentales
    - Cliquer sur "Ajouter..."
        - Nom : INRA
        - URL : http://??????????????? **TODO**
        - Authentification: (Laisser vide)
        - Activé : On
  - *Onglet->Toutes
    - Chercher : "Chloe - landscape metrics"
        - Installer ce dernier



### Installation via les sources

Se déplacer dans le dossier python/plugins de QGIS
Sous windows
```bash
C:\Users\MonUtilisateur\.qgis2\python\plugins
```

Sous linux :
```bash
cd ~/.qgis2/python/plugins/Chloe
```

Faire un ```git clone``` pour récupérer les sources
```bash
git clone https://github.com/hboussard/chloe_qgis.git
```

Démarer QGIS


## Activation/configuration du plugin

Sous QGIS, effectuer les étapes suivantes:

- *Menu->Traitement->Options
  - Fournisseures de traitements->Chloe - métriques paysagèes
    - Activate: Doit être **activé**
    - Path java exe: Sous windows, renseigner le chemin du fichier java.exe (inclure le fichier java.exe dans le chemin)
    

