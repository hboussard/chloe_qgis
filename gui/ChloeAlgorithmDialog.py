
# -*- coding: utf-8 -*-
"""
***************************************************************************
    ChloeAlgorithmDialog.py
    ---------------------
    # Date                 : May 2015

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = 'Jean-Charles Naud'
__date__ = 'May 2015'
__copyright__ = '(C) 2015, Jean-Charles Naud'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import glob
from qgis.core                          import QgsMapLayerRegistry, QgsRasterLayer
from qgis.PyQt.QtWidgets                import QWidget, QLayout, QVBoxLayout, QPushButton, QLabel, QPlainTextEdit, QLineEdit, QComboBox, QCheckBox
from processing.gui.AlgorithmDialog     import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.core.outputs            import OutputDirectory
from processing.gui.ParametersPanel     import ParametersPanel
from processing.gui.MultipleInputPanel  import MultipleInputPanel
from processing.gui.NumberInputPanel    import NumberInputPanel
from processing.core.parameters         import ParameterString, ParameterRaster
from .ValuesSelectionPanel              import ValuesSelectionPanel
from .components.CustomInputLayerSelectorPanel import CustomInputLayerSelectorPanel
from .components.AboutDialog            import AboutDialog

from PyQt4.QtCore import *

from processing.tools import dataobjects
from processing.core.outputs import OutputRaster, OutputTable
from qgis.utils import iface

from ..ChloeUtils     import ChloeUtils

class ChloeAlgorithmDialog(AlgorithmDialog):

    def __init__(self, alg):
        AlgorithmDialog.__init__(self, alg)
        QgsMapLayerRegistry.instance().layerWasAdded.connect(self.mainWidget.layerAdded)
        QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.mainWidget.layersWillBeRemoved)

    def accept(self):
        AlgorithmDialog.accept(self)
        # handling output when to be loaded
        for out in self.alg.outputs:
            if isinstance(out, (OutputRaster)) and out.open:
                layer = dataobjects.getObjectFromUri(out.value)
                if layer:
                    # test if an explicite name has been given for the layer
                    name = self.alg.name
                    if (out.name in self.alg.namedOutputs):
                      name = self.alg.namedOutputs[out.name]
                    layer.setName(name)
                    ChloeUtils.setLayerSymbology(layer, 'continuous.qml')
                    iface.legendInterface().refreshLayerSymbology(layer)
            elif isinstance(out, (OutputTable)) and out.open:
              table = dataobjects.getObjectFromUri(out.value)
              if table:
                name = self.alg.name + '_csv'
                if (out.name in self.alg.namedOutputs):
                  name = self.alg.namedOutputs[out.name]
                table.setName(name)
            
            if isinstance(out, OutputDirectory):

                # === import all asc for multi algorithm
                open_all_asc = self.alg.getParameterValue('OPEN_ALL_ASC')
                output_dir = self.alg.getOutputValue('OUTPUT_DIR').encode('utf-8')
                if self.alg.open_all_asc:
                    for file in glob.glob(output_dir+"/*.asc"):
                        load_it = QgsRasterLayer(file, os.path.splitext(os.path.basename(file))[0])
                        QgsMapLayerRegistry.instance().addMapLayer(load_it)
                        ChloeUtils.setLayerSymbology(load_it, 'continuous.qml')

        self.close()
    
    def closeEvent(self, evt):
        try:
          QgsMapLayerRegistry.instance().layerWasAdded.disconnect(self.mainWidget.layerAdded)
          QgsMapLayerRegistry.instance().layersWillBeRemoved.disconnect(self.mainWidget.layersWillBeRemoved)
        except Exception: 
          pass
        
    def addAbout(self, layout, name):
        pbAbout = QPushButton(name)
        layout.addWidget(pbAbout)
        self.about = AboutDialog()
        pbAbout.clicked.connect(self.about.run)
        
class ChloeParametersPanel(ParametersPanel):

    def __init__(self, parent, alg):
        ParametersPanel.__init__(self, parent, alg) ## Création le l'interface Qt pour les paramètres
        
        ## Add console command
        w = QWidget()              # New Qt Windows

        layout = QVBoxLayout()     # New Qt vertical Layout
        layout.setMargin(0)
        layout.setSpacing(6)

        label = QLabel()           # New Qt label (text)
        label.setText(self.tr("Chloe/Java console call"))
        layout.addWidget(label)    # Add label in layout

        self.text = QPlainTextEdit()  # New Qt champs de text in/out
        self.text.setReadOnly(True)   # Read only
        layout.addWidget(self.text)   # Add in layout

        w.setLayout(layout)           # layout -in-> Windows
        self.layoutMain.addWidget(w)  # windows -in-> Windows system

        self.connectParameterSignals()
        self.parametersHaveChanged()

    def connectParameterSignals(self):
        for w in self.widgets.values():
            if isinstance(w, QLineEdit):
                w.textChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, QComboBox):
                w.currentIndexChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, QCheckBox):
                w.stateChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, MultipleInputPanel):
                w.selectionChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, NumberInputPanel):
                w.hasChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, ValuesSelectionPanel):
                w.leText.textChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, CustomInputLayerSelectorPanel):
                w.currentIndexChanged.connect(self.parametersHaveChanged)
                w.currentIndexChanged.connect(self.cleanFieldDependent) # Clean 

        # Update console display
        self.valueItems["SAVE_PROPERTIES"].leText.textChanged.connect(self.parametersHaveChanged)

    #@pyqtSlot(str)
    def cleanFieldDependent(self):
        """
        cleanFieldDependent
        When receiving signal, clean 'leText' of QWidget selectionned
        """
        for w in self.widgets.values():
            if isinstance(w, ValuesSelectionPanel):
                w.leText.setText("")
                

    #@pyqtSlot(str)
    def parametersHaveChanged(self):

        try:

            self.parent.setParamValues()

            for output in self.alg.outputs:  # Manage output fileds
                if output.value is None:
                    output.value = self.tr("[temporary file]")

            properties = self.valueItems["SAVE_PROPERTIES"].leText.text()
            commands = self.alg.getConsoleCommands(properties)
            commands = [c for c in commands if c not in ['cmd.exe', '/C ']]
            self.text.setPlainText(" ".join(commands))
        except AlgorithmDialogBase.InvalidParameterValue as e:
            self.text.setPlainText(self.tr("Invalid value for parameter '%s'") % e.parameter.description)
        except Exception as e:
            self.text.setPlainText("Error : " + e.message)



    def getWidgetFromParameter(self, param):
        """
        Overload for custom Qwidget(Panel) from Parameter
        return item : Qwidget(Panel)
        """

        if isinstance(param, ParameterString) and param.name in ["VALUES_RANGES"]:
            # === Overload ParameterString for special parameter name like VALUES_RANGES,..

            if param.name == "VALUES_RANGES":
                item = ValuesSelectionPanel(self.parent, self.alg, param.default)

                if param.default:
                    item.setText(unicode(param.default))

        elif isinstance(param, ParameterRaster): 
            # === Overload of Panel for Raster in order to add signal for updating param

            layers = dataobjects.getRasterLayers()
            items = []
            if param.optional:
                items.append((self.NOT_SELECTED, None))
            for layer in layers:
                items.append((self.getExtendedLayerName(layer), layer))
            item = CustomInputLayerSelectorPanel(items, param)

        else:
            # == default Wigdet from Parameter, i.e. use parent method
            item = ParametersPanel.getWidgetFromParameter(self,param)

        return item
