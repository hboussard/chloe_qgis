
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
from processing.gui.NumberInputPanel    import NumberInputPanel
from processing.gui.FileSelectionPanel  import FileSelectionPanel
from processing.core.parameters         import ParameterString, ParameterRaster, ParameterFile
from processing.gui.InputLayerSelectorPanel import InputLayerSelectorPanel
from .ListSelectionPanel                import ListSelectionPanel
from .ChloeAlgorithmDialog import ChloeAlgorithmDialog
from .ChloeAlgorithmDialog import ChloeParametersPanel

from processing.core.outputs import OutputRaster, OutputVector, OutputTable




from processing.tools import dataobjects


class MapMultiAlgorithmDialog(ChloeAlgorithmDialog):

    def __init__(self, alg):
        AlgorithmDialogBase.__init__(self, alg)

        self.alg = alg

        self.mainWidget = MapMultiParametersPanel(self, alg) # Main parameter windows

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

        QgsMapLayerRegistry.instance().layerWasAdded.connect(self.mainWidget.layerAdded)
        QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.mainWidget.layersWillBeRemoved)

        self.resize(self.size().width(), self.size().height()-100) # widows heigth - 100 pixel

    def setParamValue(self, param, widget, alg=None):
        """
        Overload of Widget-to->param update mecanisme
        """
        if isinstance(widget, ListSelectionPanel):
            text = widget.text()
            return param.setValue(text)
        else:
            return AlgorithmDialog.setParamValue(self, param, widget, alg)
        

class MapMultiParametersPanel(ChloeParametersPanel):

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

        # === Init cbFilter
        cbFilter = self.widgets["METRICS"].cbFilter
        cbFilter.addItems(self.alg.types_of_metrics.keys())

        # === Init listSrc
        value = cbFilter.currentText()
        listSrc = self.widgets["METRICS"].listSrc
        listSrc.clear()
        listSrc.addItems(self.alg.types_of_metrics[value])

        # === Init listDest
        listDest = self.widgets["METRICS"].listDest
        listDest.clear()

        self.metrics_selected = set()

        lineEdit = self.widgets["METRICS"].lineEdit
        lineEdit.setReadOnly(True)


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
            elif isinstance(w, FileSelectionPanel):
                w.cmbText.currentIndexChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, InputLayerSelectorPanel):
                w.cmbText.currentIndexChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, ListSelectionPanel):
                w.pbRight.clicked.connect(self.addInListDst)
                w.listSrc.itemDoubleClicked.connect(self.addInListDst)
                w.pbLeft.clicked.connect(self.removeInListDst)
                w.pbAll.clicked.connect(self.addAllInListDst)
                w.pbClear.clicked.connect(self.removeAllListDst)
                w.lineEdit.textChanged.connect(self.parametersHaveChanged)

        # Update console display
        self.valueItems["SAVE_PROPERTIES"].leText.textChanged.connect(self.parametersHaveChanged)
        
        w = self.widgets["METRICS"].cbFilter
        w.currentIndexChanged.connect(self.changeMetricDependent)

    @staticmethod
    def iterAllItems(lws):
        for i in range(lws.count()):
            yield lws.item(i)

    #@pyqtSlot(str)
    def addAllInListDst(self):
        self.addInListDst(all=True)


    #@pyqtSlot(str)
    def addInListDst(self,item=None,all=False):
        """Add metrics selected in listSrc to ListDst"""
        if not all:
            selected = self.widgets["METRICS"].listSrc.selectedItems()
        else:
            selected = self.iterAllItems(self.widgets["METRICS"].listSrc)
        for lw in selected:
            self.metrics_selected.add(lw.text())

        listDest = self.widgets["METRICS"].listDest
        listDest.clear()
        listDest.addItems(list(self.metrics_selected))
        self.updateMetricsLigneEdit()

    #@pyqtSlot()
    def removeAllListDst(self):
        listDest = self.widgets["METRICS"].listDest
        listDest.clear()
        self.metrics_selected = set()
        self.updateMetricsLigneEdit()

    #@pyqtSlot(str)
    def removeInListDst(self):
        """Remove metrics selected in listDest"""
        selected = self.widgets["METRICS"].listDest.selectedItems()
        for lw in selected:
            self.metrics_selected.remove(lw.text())

        listDest = self.widgets["METRICS"].listDest
        listDest.clear()
        listDest.addItems(list(self.metrics_selected))
        self.updateMetricsLigneEdit()

 
    def updateMetricsLigneEdit(self):
        """update Metrics (QLineEdit in readOnly mode)"""
        lineEdit = self.widgets["METRICS"].lineEdit
        metrics = list(self.metrics_selected)
        if metrics:
            lineEdit.setText(";".join(metrics))
        else:
            lineEdit.setText("")

    #@pyqtSlot(str)
    def changeMetricDependent(self):
        """
        Update metric source list when the filter of metric change
        """
        cbFilter = self.widgets["METRICS"].cbFilter
        
        # === Init list metric
        value = cbFilter.currentText()
        listSrc = self.widgets["METRICS"].listSrc
        listSrc.clear()
        listSrc.addItems(self.alg.types_of_metrics[value])



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
            #raise e



    def getWidgetFromParameter(self, param):
        """
        Overload for custom Qwidget(Panel) from Parameter
        return item : Qwidget(Panel)
        """

        if param.name in ["METRICS"]:
            # === Overload ParameterString for special parameter name like FIELDS,..s
            item = ListSelectionPanel(self.parent, self.alg, param.default)


        else:
            # == default Wigdet from Parameter, i.e. use parent method
            item = ParametersPanel.getWidgetFromParameter(self,param)

        return item
