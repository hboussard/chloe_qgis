# Documentation pour développeur


## Traduction

Les traductions passe par les étapes suivantes:
- Génération/Update du fichier "i18n/Chole_fr_FR.ts" contenant les traduction sous forme XML
- Éditer le fichier TS avec un éditeur
- Générer le fichier "i18n/Chole_fr_FR.qm"

### Fichier TS (XML de traduction)
La génération et l'udape du fichier .ts se fait sous linux avec
Génération/Update du fichier TS (XML de traduction) avec lupdate

En root, sous linux, installer qt4-linguist-tools
```bash
apt-get install qt4-linguist-tools
```

En tant qu'utilisateur (à la racine du projet)
Afficher l'aide 
```bash
pylupdate4 -help
```

Génération/Update du fichier .ts
```bash
pylupdate4 -verbose ./i18n/Chloe_fr_FR.pro 
```


### Editer la traduction (.ts) avec Linguist
```bash
/usr/bin/qtchooser --run-tool=linguist -qt=4
```

- File->Open
  - Selectionner le fichier de traduction ./i18n/Chloe_fr.ts


### Fichier QML (archive optimisée de traduction)
Générer le ficheir .qml
```bash
/usr/bin/qtchooser --run-tool=lrelease -qt=4  ./i18n/Chloe_fr_FR.pro 
```
