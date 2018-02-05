
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


from qgis.core import QgsMapLayerRegistry, QgsRasterLayer
from qgis.PyQt.QtWidgets import QWidget, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QLineEdit, QComboBox, QCheckBox
from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel    import NumberInputPanel
from processing.gui.FileSelectionPanel  import FileSelectionPanel
from processing.core.parameters         import ParameterString, ParameterRaster, ParameterFile
from processing.gui.InputLayerSelectorPanel import InputLayerSelectorPanel
from .ListSelectionPanel   import ListSelectionPanel
from .IntListSelectionPanel import IntListSelectionPanel
from .ValuesSelectionPanel import ValuesSelectionPanel
from .ChloeAlgorithmDialog import ChloeAlgorithmDialog
from .ChloeAlgorithmDialog import ChloeParametersPanel

from processing.core.outputs import OutputRaster, OutputVector, OutputTable

from processing.tools import dataobjects

from ..ChloeUtils import ChloeUtils

class SelectedMultiAlgorithmDialog(ChloeAlgorithmDialog):

    def __init__(self, alg):
        AlgorithmDialogBase.__init__(self, alg)

        self.alg = alg

        self.mainWidget = SelectedMultiParametersPanel(self, alg) # Main parameter windows

        self.setMainWidget()   # Create default Qt interface

        cornerWidget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        self.tabWidget.setStyleSheet("QTabBar::tab { height: 30px; }")
        runAsBatchButton = QPushButton(self.tr("Run as batch process...")) # New button "Run as Batch"
        runAsBatchButton.clicked.connect(self.runAsBatch)
        layout.addWidget(runAsBatchButton)
        self.addAbout(layout)

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
        elif isinstance(widget, ValuesSelectionPanel):
            text = widget.text()
            return param.setValue(text)
        else:
            return AlgorithmDialog.setParamValue(self, param, widget, alg)
        
class SelectedMultiParametersPanel(ChloeParametersPanel):

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

        self.types_of_metrics = {}

        for output in self.alg.outputs:
            if isinstance(output, (OutputRaster, OutputVector, OutputTable)):
                self.checkBoxes[output.name].setText(self.tr('Open output file after running algorithm'))


        self.connectParameterSignals()
        self.parametersHaveChanged()

        self.changePixelsPointsSelectDependent()
        self.changeWindowShapeDependent()

        # === param:WINDOW_SIZES Widget:IntListSelectionPanel ===
        lineEdit = self.widgets["WINDOW_SIZES"].lineEdit
        lineEdit.setReadOnly(True)
        sbInt = self.widgets["WINDOW_SIZES"].sbInt
        sbInt.setValue(3)

        # === param:METRICS Widget:ListSelectionPanel ===
        # === Init cbFilter
        cbFilter = self.widgets["METRICS"].cbFilter
        cbFilter.addItems(self.alg.types_of_metrics.keys())

        # === Init listSrc
        value = cbFilter.currentText()
        listSrc = self.widgets["METRICS"].listSrc
        listSrc.clear()
        if self.types_of_metrics:
            if value in self.types_of_metrics.keys():
                listSrc.addItems(self.types_of_metrics[value])
        #for m in self.alg.types_of_metrics[value]:
        #    listSrc.append(m)

        # === Init listDest
        listDest = self.widgets["METRICS"].listDest
        listDest.clear()

        self.metrics_selected = set()
        self.window_sizes_selected = set()

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
                w.leText.textChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, InputLayerSelectorPanel):
                w.cmbText.currentIndexChanged.connect(self.initCalculateMetric)
                w.cmbText.currentIndexChanged.connect(self.parametersHaveChanged)
                w.cmbText.currentIndexChanged.connect(self.removeAllListDst)
                w.cmbText.currentIndexChanged.connect(self.changeMetricDependent)
            elif isinstance(w, IntListSelectionPanel):
                w.pbRight.clicked.connect(self.addIntInListDst)
                w.pbRemove.clicked.connect(self.removeIntInListDst)
                w.pbClear.clicked.connect(self.removeIntAllListDst)
                w.lineEdit.textChanged.connect(self.parametersHaveChanged)
            elif isinstance(w, ListSelectionPanel):
                w.pbRight.clicked.connect(self.addInListDst)
                w.listSrc.itemDoubleClicked.connect(self.addInListDst)
                w.pbLeft.clicked.connect(self.removeInListDst)
                w.pbAll.clicked.connect(self.addAllInListDst)
                w.pbClear.clicked.connect(self.removeAllListDst)
                w.lineEdit.textChanged.connect(self.parametersHaveChanged)
                w.cbFilter.currentIndexChanged.connect(self.changeMetricDependent)
            elif isinstance(w, ValuesSelectionPanel):
                w.leText.textChanged.connect(self.parametersHaveChanged)

        
        w = self.widgets["WINDOW_SHAPE"]
        w.currentIndexChanged.connect(self.changeWindowShapeDependent)
        w = self.widgets["WINDOW_SIZES"]
        w.sbInt.setSingleStep(2)  # step incrementation and decrementation
        w = self.widgets["METRICS"].cbFilter
        w.currentIndexChanged.emit(0)

        w = self.widgets["PIXELS_POINTS_SELECT"]    
        w.currentIndexChanged.connect(self.changePixelsPointsSelectDependent)

        # Update console display
        self.valueItems["SAVE_PROPERTIES"].leText.textChanged.connect(self.parametersHaveChanged)

        self.widgets["INPUT_LAYER_ASC"].cmbText.currentIndexChanged.emit(0)


    #@pyqtSlot(str)
    def initCalculateMetric(self):
        w = self.widgets['INPUT_LAYER_ASC']
        if isinstance(w.getValue(), QgsRasterLayer):
            rasterLayerParam = w.getValue().source().encode('utf-8')
        else:
            rasterLayerParam = w.getValue().encode('utf-8')
        
        int_values_and_nodata = ChloeUtils.extractValueNotNull(rasterLayerParam)

        self.types_of_metrics = ChloeUtils.calculateMetric(
            self.alg.types_of_metrics,
            self.alg.types_of_metrics_simple,
            self.alg.types_of_metrics_cross,
            int_values_and_nodata
        )


    # === param:PIXELS_POINTS_SELECT Widget:ComboBox
    #@pyqtSlot(str)
    def changePixelsPointsSelectDependent(self):

        index = self.widgets["PIXELS_POINTS_SELECT"].currentIndex()
        if index == 0:   # pixel(s) file
            self.widgets["PIXELS_FILE"].leText.setDisabled(False)
            self.widgets["POINTS_FILE"].leText.setDisabled(True)
        elif index == 1: # point(s) file
            self.widgets["PIXELS_FILE"].leText.setDisabled(True)
            self.widgets["POINTS_FILE"].leText.setDisabled(False)

    # === param:WINDOW_SHAPE Widget:ComboBox
    #@pyqtSlot(str)
    def changeWindowShapeDependent(self):
        txt = self.widgets["WINDOW_SHAPE"].currentText()
        if txt == "FUNCTIONAL":
            self.widgets["FRICTION_FILE"].setEnabled(True)
        else:
            self.widgets["FRICTION_FILE"].setDisabled(True)

    # === param:WINDOW_SIZES Widget:IntListSelectionPanel ===

    #@pyqtSlot(str)
    def addIntInListDst(self):
        """Add grid size integer in listSrc"""
        int_value = self.widgets["WINDOW_SIZES"].sbInt.value()

        #if len(self.window_sizes_selected) == 0:                  # constraint V1.0: "select only one"
        self.window_sizes_selected.add(str(int_value))

        listDest = self.widgets["WINDOW_SIZES"].listDest
        listDest.clear()
        listDest.addItems(list(self.window_sizes_selected))
        self.updateWindowsSizesLigneEdit()

    #@pyqtSlot()
    def removeIntAllListDst(self):
        """Remove all grid sizes in listDest"""
        listDest = self.widgets["WINDOW_SIZES"].listDest
        listDest.clear()
        self.window_sizes_selected = set()
        self.updateWindowsSizesLigneEdit()

    #@pyqtSlot(str)
    def removeIntInListDst(self):
        """Remove grid sizes selected in listDest"""
        selected = self.widgets["WINDOW_SIZES"].listDest.selectedItems()
        for lw in selected:
            self.window_sizes_selected.remove(lw.text())

        listDest = self.widgets["WINDOW_SIZES"].listDest
        listDest.clear()
        listDest.addItems(list(self.window_sizes_selected))
        self.updateWindowsSizesLigneEdit()

 
    def updateWindowsSizesLigneEdit(self):
        """update Gris sizes (QLineEdit in readOnly mode)"""
        lineEdit = self.widgets["WINDOW_SIZES"].lineEdit
        WINDOW_SIZES = list(self.window_sizes_selected)
        if WINDOW_SIZES:
            lineEdit.setText(";".join(WINDOW_SIZES))
        else:
            lineEdit.setText("")


    # === param:METRICS Widget:ListSelectionPanel ===

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
        if self.types_of_metrics:
            if value in self.types_of_metrics.keys():
                listSrc.addItems(self.types_of_metrics[value])

    # == One parameter have changed ==
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

        if param.name in ["WINDOW_SIZES"]:
            # === Overload ParameterString for special parameter name like FIELDS,..s
            item = IntListSelectionPanel(self.parent, self.alg, param.default)

        elif param.name in ["METRICS"]:
            # === Overload ParameterString for special parameter name like FIELDS,..s
            item = ListSelectionPanel(self.parent, self.alg, param.default)
        elif param.name in ["FILTER", "UNFILTER"]:
            # === Overload ParameterString for special parameter name like FIELDS,..s
            item = ValuesSelectionPanel(self.parent, self.alg, param.default,'INPUT_LAYER_ASC')
            if param.default:
                item.setText(unicode(param.default))

        else:
            # == default Wigdet from Parameter, i.e. use parent method
            item = ParametersPanel.getWidgetFromParameter(self,param)

        return item
