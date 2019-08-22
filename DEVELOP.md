

```
pip install pylint graphviz pydot
```
install graphviz:  https://graphviz.gitlab.io/download/
Add C:\Program Files (x86)\Graphviz2.38\bin in PATH env

pyreverse -p ProcessingPlugin "C:\var\install\QGIS 3.4\apps\qgis\python\plugins\processing\ProcessingPlugin.py"

dot -Tpng classes_ProcessingPlugin.dot -o classes_ProcessingPlugin.png


install ghostscript: https://www.ghostscript.com/download/gsdnld.html





pyreverse -ASmy -p core "C:\var\install\QGIS 3.4\apps\qgis\python\plugins\processing\core"
dot -Tpng classes_All.dot -o classes_All.png



pyreverse -ASmy -p processing "C:\var\install\QGIS 3.4\apps\qgis\python\plugins\processing
dot -Tpng classes_processing.dot -o classes_processing.png


pyreverse -ASmy -p core "C:\var\install\QGIS 3.4\apps\qgis\python\plugins\processing\core
dot -Tpng classes_core.dot -o classes_core.png

dot -Tpng packages_core.dot -o packages_core.png
