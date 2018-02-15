
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
from qgis.PyQt.QtWidgets import QWidget, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QLineEdit, QComboBox, QCheckBox,QTableWidgetItem
from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel    import NumberInputPanel
from processing.gui.FileSelectionPanel  import FileSelectionPanel
from processing.core.parameters         import ParameterString, ParameterRaster, ParameterFile
from processing.gui.InputLayerSelectorPanel import InputLayerSelectorPanel
from .ListSelectionPanel    import ListSelectionPanel
from .IntListSelectionPanel import IntListSelectionPanel
from .ValuesSelectionPanel  import ValuesSelectionPanel
from .ChloeAlgorithmDialog  import ChloeAlgorithmDialog
from .ChloeAlgorithmDialog  import ChloeParametersPanel

from processing.tools import dataobjects
from .components.TableReplaceInputDialog import TableReplaceInputDialog
from .components. FileSelectionCSVTXTPanel import FileSelectionCSVTXTPanel

from processing.core.outputs import OutputRaster, OutputVector, OutputTable

import os
from osgeo import gdal
import numpy as np
import math
import re
class SearchAndReplaceAlgorithmDialog(ChloeAlgorithmDialog):

    def __init__(self, alg):
        AlgorithmDialogBase.__init__(self, alg)

        self.alg = alg

        self.mainWidget = SearchAndReplaceParametersPanel(self, alg) # Main parameter windows

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

        self.mainWidget.parametersHaveChanged()

        QgsMapLayerRegistry.instance().layerWasAdded.connect(self.mainWidget.layerAdded)
        QgsMapLayerRegistry.instance().layersWillBeRemoved.connect(self.mainWidget.layersWillBeRemoved)

        # First run parameter changed, i.e. update value widget-to->param

        self.resize(self.size().width(), self.size().height()-100) # widows heigth - 100 pixel
        

    def setParamValue(self, param, widget, alg=None):
        """
        Overload of Widget-to->param update mecanisme
        """
        if isinstance(widget, TableReplaceInputDialog):
            text = widget.text()
            return param.setValue(text)
        else:
            return AlgorithmDialog.setParamValue(self, param, widget, alg)
        
class SearchAndReplaceParametersPanel(ChloeParametersPanel):

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
        self.changeInputDependent()

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
                w.cmbText.currentIndexChanged.connect(self.parametersHaveChanged)
                w.cmbText.currentIndexChanged.connect(self.changeInputDependent)
            elif isinstance(w, TableReplaceInputDialog):
                w.leText.textChanged.connect(self.parametersHaveChanged)

        w = self.widgets['MAP_CSV']
        w.leText.textChanged.connect(self.updateDependantMapCSV)

        w = self.widgets['CHANGES']
        w.pbApply.clicked.connect(self.applyCSVMap)

        # Update console display
        self.valueItems["SAVE_PROPERTIES"].leText.textChanged.connect(self.parametersHaveChanged)

    #@pyqtSlot(str)
    def changeInputDependent(self):
        w = self.widgets['INPUT_LAYER_ASC']
        if isinstance(w.getValue(), QgsRasterLayer):
            rasterLayerParam = w.getValue().source().encode('utf-8')
        else:
            rasterLayerParam = w.getValue().encode('utf-8')

        # == Clean table
        w = self.widgets['CHANGES']
        wt = w.twAssociation
        for row in xrange(0,wt.rowCount()):
            r0 = wt.item(row,0) 
            r1 = wt.item(row,1)
            if isinstance(r0, QTableWidgetItem):
                r0.setText("")
            else:
                wt.setItem(row,0,QTableWidgetItem(""))
            if isinstance(r1, QTableWidgetItem):
                r1.setText("")
            else:
                wt.setItem(row,1,QTableWidgetItem(""))

        try:
            if rasterLayerParam:
                f_input = rasterLayerParam

                # === Parse asc value
                ds = gdal.Open(f_input)                 # DataSet
                band =  ds.GetRasterBand(1)             # -> band
                array = np.array(band.ReadAsArray())    # -> matrice values
                values = np.unique(array)
                values_and_nodata = np.insert(values, 0, band.GetNoDataValue()) # Add nodata values in numpy array
                int_values_and_nodata = [int(math.floor(x)) for x in values_and_nodata ]
                
        
                # == Write value in table
                wt = w.twAssociation
                int_values_and_nodata


                for val, row in zip(int_values_and_nodata,xrange(0,wt.rowCount())):
                    r0 = wt.item(row,0)
                    
                    if isinstance(r0, QTableWidgetItem):
                        r0.setText(str(val))
                    else:
                        wt.setItem(row,0,QTableWidgetItem(str(val)))
                    
        except:
            pass


    #@pyqtSlot(str)
    def updateDependantMapCSV(self):
        w = self.widgets['MAP_CSV']
        f_map_csv =  w.leText.text().encode('utf-8')
        w_change = self.widgets['CHANGES']
        cmbBox = w_change.cmbBox
        cmbBox.clear()

        try:
            # == Get list index
            if f_map_csv:
                if os.path.exists(f_map_csv):
                    with open(f_map_csv, 'r') as f:
                        line = f.next()
                    headers = filter(None, re.split('\n|;| |,', line))
                    cmbBox.addItems(headers[1:])
        except:
            pass


    #@pyqtSlot(str)
    def applyCSVMap(self):
        w = self.widgets['MAP_CSV']
        f_map_csv =  w.leText.text().encode('utf-8')
        w_change = self.widgets['CHANGES']

        # Index
        if f_map_csv:
            if os.path.exists(f_map_csv):
                with open(f_map_csv, 'r') as f:
                    line = f.next()
                headers = filter(None, re.split('\n|;| |,', line))
                name_col = w_change.cmbBox.currentText()
                idex_col = headers[1:].index(name_col) +1


        t_ass =[] # Table d'association
        if f_map_csv:
            if os.path.exists(f_map_csv):
                with open(f_map_csv, 'r') as f:
                    b_header = 1
                    
                    for line in f:
                        if b_header == 1:
                            b_header = 0
                            continue   # Jump the header
                        data = filter(None, re.split('\n|;| |,', line))
                        t_ass.append([data[0],data[idex_col]]) # Table two dimention

        
        if t_ass:   # Update with associtation table
            wt = w_change.twAssociation
            for t_as in t_ass:
                val_old = t_as[0]
                val_new = t_as[1]
                for row in xrange(0,wt.rowCount()):
                    r0 = wt.item(row,0)
                    if r0:
                        if r0.text() == str(val_old):
                            # Update value
                            r1 = wt.item(row,1)
                            if isinstance(r1, QTableWidgetItem):        
                                r1.setText(str(val_new))
                            else:
                                wt.setItem(row,1,QTableWidgetItem(str(val_new)))



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

        if param.name in ["CHANGES"]:
            item = TableReplaceInputDialog(self,param)

        elif param.name in ["MAP_CSV"]:
            item = FileSelectionCSVTXTPanel(param.isFolder, param.ext)
        else:
            # == default Wigdet from Parameter, i.e. use parent method
            item = ParametersPanel.getWidgetFromParameter(self,param)

        return item
