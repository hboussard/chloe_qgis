
# -*- coding: utf-8 -*-

"""
***************************************************************************
    ChloeAlgorithmDialog.py
    ---------------------
    Date                 : May 2015

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = 'Jean-Charles Naud'
__date__ = 'May 2015'
__copyright__ = '(C) 2015, Jean-Charles Naud'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


from qgis.core import QgsMapLayerRegistry
from qgis.PyQt.QtWidgets import QWidget, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QLineEdit, QComboBox, QCheckBox
from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel import NumberInputPanel
from processing.core.parameters import ParameterString, ParameterRaster
from .ValuesSelectionPanel import ValuesSelectionPanel
from .components.CustomInputLayerSelectorPanel import CustomInputLayerSelectorPanel

from .ChloeAlgorithmDialog import ChloeAlgorithmDialog
from .ChloeAlgorithmDialog import ChloeParametersPanel

from processing.core.outputs import OutputRaster, OutputVector, OutputTable


from processing.tools import dataobjects


class DistanceAlgorithmDialog(ChloeAlgorithmDialog):

    def __init__(self, alg):
        AlgorithmDialogBase.__init__(self, alg)

        self.alg = alg

        self.mainWidget = DistanceParametersPanel(self, alg) # Main parameter windows

        self.setMainWidget()   # Create default Qt interface

        cornerWidget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        self.tabWidget.setStyleSheet("QTabBar::tab { height: 30px; }")
        runAsBatchButton = QPushButton(self.tr("Run as batch process...")) # New button "Run as Batch"
        runAsBatchButton.clicked.connect(self.runAsBatch)
        layout.addWidget(runAsBatchButton)
        self.addAbout(layout, self.tr("About"))

        cornerWidget.setLayout(layout)                # Add layout -in-> QWidget

        self.tabWidget.setCornerWidget(cornerWidget)  # Add QWidget -> in tab

        self.mainWidget.parametersHaveChanged()       # First run parameter changed, i.e. update value widget-to->param

        self.resize(self.size().width(), self.size().height()-100) # widows heigth - 100 pixel

    def setParamValue(self, param, widget, alg=None):
        """
        Overload of Widget-to->param update mecanisme
        """

        if isinstance(widget, ValuesSelectionPanel):
            text = widget.leText.text()
            return param.setValue(text)
        else:
            return AlgorithmDialog.setParamValue(self, param, widget, alg)
        

class DistanceParametersPanel(ChloeParametersPanel):

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

        for output in self.alg.outputs:
            if isinstance(output, (OutputRaster, OutputVector, OutputTable)):
                self.checkBoxes[output.name].setText(self.tr('Open output file after running algorithm'))

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

            # === Update values of widgets-to->params ===
            #  For custom widget (like CustomPanel), overload AlgorithmDialog.setParamValue()
            #  Important, can lunch exception if value is 'null' and 'required'
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

        if  param.name in ["VALUES_RANGES"]:
            # === Overload ParameterString for special parameter name like VALUES_RANGES,..
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
