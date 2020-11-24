# -*- coding: utf-8 -*-

"""
***************************************************************************
    chloe_algorithm_dialog.py
    ---------------------
    Date                 : May 2015
    Copyright            : (C) 2015 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Jean-Charles Naud/Alkante'
__date__ = 'May 2015'
__copyright__ = '(C) 2015, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from functools import partial

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (QWidget,
                                 QVBoxLayout,
                                 QPushButton,
                                 QLabel,
                                 QPlainTextEdit,
                                 QLineEdit,
                                 QComboBox,
                                 QCheckBox,
                                 QSizePolicy,
                                 QDialogButtonBox,
                                 QFileDialog,
                                 QSpinBox)

from qgis.core import (QgsProcessingFeedback,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterString,
                       QgsSettings)
from qgis.gui import (QgsMessageBar,
                      QgsProjectionSelectionWidget,
                      QgsProcessingAlgorithmDialogBase)

from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel import NumberInputPanel
from processing.gui.DestinationSelectionPanel import DestinationSelectionPanel
from processing.gui.FileSelectionPanel import FileSelectionPanel
from processing.gui.wrappers import (WidgetWrapper, 
                                     EnumWidgetWrapper)
from processing.tools.dataobjects import createContext

from pprint import pformat
import time

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton, QSizePolicy, QDialogButtonBox
from qgis.PyQt.QtGui import QColor, QPalette

from qgis.core import (Qgis,
                       QgsProject,
                       QgsApplication,
                       QgsProcessingUtils,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingAlgRunnerTask,
                       QgsProcessingOutputHtml,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingOutputLayerDefinition,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsTaskManager,
                       QgsMessageLog,)
from qgis.gui import (QgsGui,
                      QgsMessageBar,
                      QgsProcessingAlgorithmDialogBase)
from qgis.utils import iface

from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.ProcessingResults import resultsList
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.BatchPanel import BatchPanel
from processing.gui.BatchAlgorithmDialog import BatchAlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.AlgorithmExecutor import executeIterating, execute#, execute_in_place
from .ChloePostProcessing import ChloehandleAlgorithmResults
from processing.gui.wrappers import WidgetWrapper

from processing.tools import dataobjects

import os
import warnings
import copy
from functools import partial

from qgis.core import (QgsProcessingParameterDefinition,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterPoint,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFileDestination,
                       QgsProject)
#from qgis.gui import (QgsProcessingContextGenerator,
                      #QgsProcessingParameterWidgetContext)
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (QWidget, QHBoxLayout, QToolButton, QComboBox,
                                 QLabel, QCheckBox, QSizePolicy)
from qgis.PyQt.QtGui import QIcon

from processing.gui.DestinationSelectionPanel import DestinationSelectionPanel
from processing.gui.wrappers import WidgetWrapperFactory, WidgetWrapper, RasterWidgetWrapper, FileWidgetWrapper
from processing.tools.dataobjects import createContext

from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER, DIALOG_BATCH, DIALOG_STANDARD

from .gui.csv_field_selection_panel import CSVFieldSelectionPanel
from .gui.values_selection_panel import ValuesSelectionPanel
from .gui.classification_table_panel import ClassificationTablePanel
from .gui.components.DialListCheckBox import DialListCheckBox
from .gui.table_replace_input_panel import TableReplaceInputPanel
from .gui.double_cmb_box_selection_panel import DoubleCmbBoxSelectionPanel
from .gui.list_selection_panel import ListSelectionPanel
from .gui.int_list_selection_panel import IntListSelectionPanel
from .gui.factor_table_panel import FactorTablePanel
from .gui.odd_even_number_spinbox import IntSpinbox

pluginPath = os.path.join(
    QgsApplication.pkgDataPath(),
    'python',
    'plugins',
    'processing')

class ChloeAlgorithmDialog(AlgorithmDialog):

    def __init__(self, alg):
        super().__init__(alg)
        self.mainWidget().parametersHaveChanged()

    def getParametersPanel(self, alg, parent):
        return ChloeParametersPanel(parent, alg)

    def accept(self):
        #print("accept")
        super().accept()
   
    def finish(self, successful, result, context, feedback):
        #print("finish...")
        super().finish(successful, result, context, feedback)
        keepOpen = not successful or ProcessingConfig.getSetting(ProcessingConfig.KEEP_DIALOG_OPEN)
        #print("keepOpen " + str(keepOpen) + "successFull " +str(successful) + str(ProcessingConfig.getSetting(ProcessingConfig.KEEP_DIALOG_OPEN)))
        if not keepOpen:
            self.close()
        else:
            self.resetGui()

    #
    # def getParameterValues(self):
    #     """OVERLOAD"""
    #     QgsMessageLog.logMessage('getParameterValues','Processing', Qgis.Info)
    #
    #     parameters = {}
    #
    #     if self.mainWidget() is None:
    #         return parameters
    #
    #     for param in self.algorithm().parameterDefinitions():
    #         if param.flags() & QgsProcessingParameterDefinition.FlagHidden:
    #             continue
    #         if not param.isDestination():
    #
    #             if self.in_place and param.name() == 'INPUT':
    #                 parameters[param.name()] = self.active_layer
    #                 continue
    #
    #             try:
    #                 wrapper = self.mainWidget().wrappers[param.name()]
    #             except KeyError:
    #                 continue
    #
    #             # For compatibility with 3.x API, we need to check whether the wrapper is
    #             # the deprecated WidgetWrapper class. If not, it's the newer
    #             # QgsAbstractProcessingParameterWidgetWrapper class
    #             # TODO QGIS 4.0 - remove
    #             if issubclass(wrapper.__class__, WidgetWrapper):
    #                 widget = wrapper.widget
    #             else:
    #                 widget = wrapper.wrappedWidget()
    #
    #             if widget is None:
    #                 continue
    #
    #             value = wrapper.parameterValue()
    #             parameters[param.name()] = value
    #
    #             if not param.checkValueIsAcceptable(value):
    #                 raise AlgorithmDialogBase.InvalidParameterValue(param, widget)
    #         else:
    #             if self.in_place and param.name() == 'OUTPUT':
    #                 parameters[param.name()] = 'memory:'
    #                 continue
    #
    #             dest_project = None
    #             if not param.flags() & QgsProcessingParameterDefinition.FlagHidden and \
    #                     isinstance(param, (QgsProcessingParameterRasterDestination,
    #                                        QgsProcessingParameterFeatureSink,
    #                                        QgsProcessingParameterVectorDestination,
    #                                        QgsProcessingParameterFileDestination)):
    #                 if not isinstance(param, QgsProcessingParameterFileDestination):
    #                     if self.mainWidget().checkBoxes[param.name()].isChecked():
    #                         dest_project = QgsProject.instance()
    #                 elif param.name() == 'OUTPUT_ASC':
    #
    #                     print('B : {}'.format(self.algorithm().output_asc_checked))
    #                     print('obj : {}'.format(self.algorithm()))
    #                     if self.mainWidget().checkBoxes[param.name()].isChecked():
    #                         self.algorithm().output_asc_checked = True
    #                         dest_project = QgsProject.instance()
    #                     else:
    #                         self.algorithm().output_asc_checked = False
    #                     print('A : {}'.format(self.algorithm().output_asc_checked))
    #             value = self.mainWidget().outputWidgets[param.name()].getValue()
    #             if value and isinstance(value, QgsProcessingOutputLayerDefinition):
    #                 value.destinationProject = dest_project
    #             elif value and isinstance(value, QgsProcessingParameterFileDestination) and param.name() == 'OUTPUT_ASC':
    #                 value.destinationProject = dest_project
    #             if value:
    #                 parameters[param.name()] = value
    #
    #     return self.algorithm().preprocessParameters(parameters)
    #
    #
    # def finish(self, successful, result, context, feedback):
    #     """Heavy overload"""
    #     feedback.pushInfo('finish')
    #     #QgsMessageLog.logMessage('finish','Processing', Qgis.Info)
    #     keepOpen = not successful or ProcessingConfig.getSetting(ProcessingConfig.KEEP_DIALOG_OPEN)
    #     #self.setInfo('ICI :{}'.fromat(self.iterateParam)) # toto
    #     if self.iterateParam is None:
    #
    #         # add html results to results dock
    #         for out in self.algorithm().outputDefinitions():
    #             if isinstance(out, QgsProcessingOutputHtml) and out.name() in result and result[out.name()]:
    #                 resultsList.addResult(icon=self.algorithm().icon(), name=out.description(), timestamp=time.localtime(),
    #                                       result=result[out.name()])
    #
    #         if not ChloehandleAlgorithmResults(self.algorithm(), context, feedback, not keepOpen):
    #             self.resetGui()
    #             return
    #
    #     self.setExecuted(True)
    #     self.setResults(result)
    #     self.setInfo(self.tr('Algorithm \'{0}\' finished').format(self.algorithm().displayName()), escapeHtml=False)
    #
    #     if not keepOpen:
    #         self.close()
    #     else:
    #         self.resetGui()
    #         if self.algorithm().hasHtmlOutputs():
    #             self.setInfo(
    #                 self.tr('HTML output has been generated by this algorithm.'
    #                         '\nOpen the results dialog to check it.'), escapeHtml=False)
    #

    def getParameterValues(self):
        parameters = super().getParameterValues()
        for param in self.algorithm().parameterDefinitions():
            if isinstance(param, 
                (ChloeCSVParameterFileDestination, 
                ChloeASCParameterFileDestination, 
                ChloeParameterFolderDestination
                )):
                paramName = param.name()
                if paramName in parameters:
                    p = parameters[paramName]
                    #print("param " + str(p))
                    toBeOpened = self.mainWidget().checkBoxes[paramName].isChecked()
                    value = self.mainWidget().outputWidgets[paramName].getValue()
                    #print("value " + str(value))
                    newValue = { "data": value, "openLayer" : toBeOpened }
                    #print("newValue " + str(newValue))
                    parameters[paramName] = newValue
        return self.algorithm().preprocessParameters(parameters)

class ChloeParametersPanel(ParametersPanel):

    def __init__(self, parent, alg):
        super().__init__(parent, alg)

        w = QWidget()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(6)
        label = QLabel()
        label.setText(self.tr("Chloe Command line"))
        layout.addWidget(label)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        w.setLayout(layout)
        self.layoutMain.addWidget(w)

        self.connectParameterSignals()
        self.parametersHaveChanged()

    # def initWidgets(self):
    #     """Init widget panel for each input output"""
    #     super().initWidgets()

        # for output_name, output_panel in self.outputWidgets.items():
        #
        #     # Add check box for automacial load after process algorithm
        #     #    for 'OUTPUT_ASC' (QgsProcessingParameterFileDestination)
        #     if output_name == 'OUTPUT_ASC':
        #         check = QCheckBox()
        #         check.setText(QCoreApplication.translate('ParametersPanel', 'Open output file after running algorithm'))
        #
        #         def skipOutputChanged(checkbox, skipped):
        #             checkbox.setEnabled(not skipped)
        #             if skipped:
        #                 checkbox.setChecked(False)
        #         check.setChecked(not output_panel.outputIsSkipped())
        #         check.setEnabled(not output_panel.outputIsSkipped())
        #
        #         output_panel.skipOutputChanged.connect(partial(skipOutputChanged, check))
        #         self.layoutMain.insertWidget(self.layoutMain.count() - 1, check)
        #         self.checkBoxes[output_name] = check

    def initWidgets(self): # Heavy overload
        # If there are advanced parameters — show corresponding groupbox
        for param in self.alg.parameterDefinitions():
            if param.flags() & QgsProcessingParameterDefinition.FlagAdvanced:
                self.grpAdvanced.show()
                break

        #widget_context = QgsProcessingParameterWidgetContext()
        #if iface is not None:
        #    widget_context.setMapCanvas(iface.mapCanvas())

        # Create widgets and put them in layouts
        for param in self.alg.parameterDefinitions():
            if param.flags() & QgsProcessingParameterDefinition.FlagHidden:
                continue

            #print('initWidgets - param.name(): {}'.format(param.name()))
            if param.isDestination(): # and param.name() != 'OUTPUT_ASC':
                continue
            else:
                wrapper = WidgetWrapperFactory.create_wrapper(param, self.parent)
                self.wrappers[param.name()] = wrapper

                #widget = wrapper.widget    

                # For compatibility with 3.x API, we need to check whether the wrapper is
                # the deprecated WidgetWrapper class. If not, it's the newer
                # QgsAbstractProcessingParameterWidgetWrapper class
                # TODO QGIS 4.0 - remove
                is_python_wrapper = issubclass(wrapper.__class__, WidgetWrapper)
                if not is_python_wrapper:
                    from qgis.gui import (QgsProcessingContextGenerator, QgsProcessingParameterWidgetContext)
                    widget_context = QgsProcessingParameterWidgetContext()
                    if iface is not None:
                        widget_context.setMapCanvas(iface.mapCanvas())
                    wrapper.setWidgetContext(widget_context)
                    widget = wrapper.createWrappedWidget(self.processing_context)
                    wrapper.registerProcessingContextGenerator(self.context_generator)
                else:
                    widget = wrapper.widget

                #if self.in_place and param.name() in ('INPUT', 'OUTPUT'):
                    # don't show the input/output parameter widgets in in-place mode
                    # we still need to CREATE them, because other wrappers may need to interact
                    # with them (e.g. those parameters which need the input layer for field
                    # selections/crs properties/etc)
                #    continue

                if widget is not None:
                    if is_python_wrapper:
                        #widget.setToolTip(param.toolTip())
                        print(param.toolTip())

                    if isinstance(param, QgsProcessingParameterFeatureSource):
                        layout = QHBoxLayout()
                        layout.setSpacing(6)
                        layout.setMargin(0)
                        layout.addWidget(widget)
                        button = QToolButton()
                        icon = QIcon(os.path.join(pluginPath, 'images', 'iterate.png'))
                        button.setIcon(icon)
                        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
                        #button.setToolTip(self.tr('Iterate over this layer, creating a separate output for every feature in the layer'))
                        button.setCheckable(True)
                        layout.addWidget(button)
                        layout.setAlignment(button, Qt.AlignTop)
                        self.iterateButtons[param.name()] = button
                        button.toggled.connect(self.buttonToggled)
                        widget = QWidget()
                        widget.setLayout(layout)

                    label = None
                    if not is_python_wrapper:
                        label = wrapper.createWrappedLabel()
                    else:
                        label = wrapper.label

                    if label is not None:
                        if param.flags() & QgsProcessingParameterDefinition.FlagAdvanced:
                            self.layoutAdvanced.addWidget(label)
                        else:
                            self.layoutMain.insertWidget(
                                self.layoutMain.count() - 2, label)
                    elif is_python_wrapper:
                        desc = param.description()
                        if isinstance(param, QgsProcessingParameterExtent):
                            desc += self.tr(' (xmin, xmax, ymin, ymax)')
                        if isinstance(param, QgsProcessingParameterPoint):
                            desc += self.tr(' (x, y)')
                        if param.flags() & QgsProcessingParameterDefinition.FlagOptional:
                            desc += self.tr(' [optional]')
                        widget.setText(desc)
                    if param.flags() & QgsProcessingParameterDefinition.FlagAdvanced:
                        self.layoutAdvanced.addWidget(widget)
                    else:
                        self.layoutMain.insertWidget(
                            self.layoutMain.count() - 2, widget)

        for output in self.alg.destinationParameterDefinitions():
            if output.flags() & QgsProcessingParameterDefinition.FlagHidden:
                continue

            #if self.in_place and param.name() in ('INPUT', 'OUTPUT'):
            #    continue

            label = QLabel(output.description())
            #print('initWidgets 2 - param.name(): {}'.format(param.name()))
            widget = DestinationSelectionPanel(output, self.alg) # TODO, overload
            self.layoutMain.insertWidget(self.layoutMain.count() - 1, label)
            self.layoutMain.insertWidget(self.layoutMain.count() - 1, widget)
            if isinstance(output, (QgsProcessingParameterRasterDestination, 
                                   QgsProcessingParameterFeatureSink, 
                                   QgsProcessingParameterVectorDestination
                                   # alk: checkboxes for Chloe handling  
                                   ,ChloeCSVParameterFileDestination,
                                   ChloeASCParameterFileDestination,
                                   ChloeParameterFolderDestination)
                                   ):
                check = QCheckBox()
                check.setText(QCoreApplication.translate('ParametersPanel', 'Open output file(s) after running algorithm'))

                def skipOutputChanged(checkbox, skipped):
                    checkbox.setEnabled(not skipped)
                    if skipped:
                        checkbox.setChecked(False)
                check.setChecked(not widget.outputIsSkipped())
                check.setEnabled(not widget.outputIsSkipped())
                widget.skipOutputChanged.connect(partial(skipOutputChanged, check))
                self.layoutMain.insertWidget(self.layoutMain.count() - 1, check)
                self.checkBoxes[output.name()] = check
                # initial state
                if hasattr(output,'addToMapDefaultState'):
                    check.setChecked(output.addToMapDefaultState)

            #widget.setToolTip(param.toolTip())
            self.outputWidgets[output.name()] = widget

        for wrapper in list(self.wrappers.values()):
            wrapper.postInitialize(list(self.wrappers.values()))
        
        
        # # alk: checkboxes for Chloe handling  
        # for output in self.alg.destinationParameterDefinitions():
        #     if output.flags() & QgsProcessingParameterDefinition.FlagHidden:
        #         continue

        #     if isinstance(output, (ChloeCSVParameterFileDestination)) or isinstance(output, (ChloeASCParameterFileDestination)):
        #         check = QCheckBox()
        #         check.setText(QCoreApplication.translate('ParametersPanel', 'Open output file(s) after running algorithm'))

        #         def skipOutputChanged(checkbox, skipped):
        #             checkbox.setEnabled(not skipped)
        #             if skipped:
        #                 checkbox.setChecked(False)
        #         check.setChecked(not widget.outputIsSkipped())
        #         check.setEnabled(not widget.outputIsSkipped())
        #         widget.skipOutputChanged.connect(partial(skipOutputChanged, check))
        #         print(str(self.layoutMain)+1)
        #         self.layoutMain.insertWidget(self.layoutMain.count() - 1, check)
        #         self.checkBoxes[output.name()] = check
                
                # # connecting alg outputLoading info with checkbox state
                # self.alg.outputLoading[output.name()] = check.isChecked()
                # def updateOutputLoadingState(alg, outputName, checkbox, state):
                #     self.alg.outputLoading[outputName] = checkbox.isChecked()
                #     print( outputName + " " + str(checkbox.isChecked()) + " " + str(self.alg.outputLoading) + " " + str(self.alg))
                #     #print(str(self.alg.parameters))
                # check.stateChanged.connect(partial(updateOutputLoadingState, self, output.name(), check))
        
        # alk: addition of wrapper special config handling
        # for dependancy between wrapper, i.e. changing the value 
        # of a FileSelectionPanel entails the update of another widget

        for k in self.wrappers:
            w = self.wrappers[k]
            if hasattr(w,'getParentWidgetConfig'):
                #print(str(w) + " "  + "getParentWidgetConfig")
                config = w.getParentWidgetConfig()
                if config != None:

                    # LINKED PARAMETER ONE
                    p = self.wrappers[config['paramName']]
                    m = getattr(w, config['refreshMethod'])
           
                    if m!=None:

                        # todo generalize valueChanged handling 
                        # to any type of widget componant
                        if isinstance(p.widget, FileSelectionPanel):
                            p.widget.leText.textChanged.connect(m)
                        elif isinstance(p, RasterWidgetWrapper):
                            try:
                                p.combo.valueChanged.connect(m) # QGIS 3.8 version
                            except:
                                p.combo.currentIndexChanged.connect(m) # QGIS LTR 3.4

                    # LINKED PARAMETER TWO
                        try:
                            p2 = self.wrappers[config['paramName2']]
                            m2 =getattr(w, config['refreshMethod2'])

                            if isinstance(p2.widget, FileSelectionPanel):
                                p2.widget.leText.textChanged.connect(m2)

                            elif isinstance(p2, RasterWidgetWrapper):
                                try:
                                    p2.combo.valueChanged.connect(m2) # QGIS 3.8 version
                                except:
                                    p2.combo.currentIndexChanged.connect(m2) # QGIS LTR 3.4
                        except:
                            pass

    def connectParameterSignals(self):
        for wrapper in list(self.wrappers.values()):
            wrapper.widgetValueHasChanged.connect(self.parametersHaveChanged)

            # TODO - remove when all wrappers correctly emit widgetValueHasChanged!

            # For compatibility with 3.x API, we need to check whether the wrapper is
            # the deprecated WidgetWrapper class. If not, it's the newer
            # QgsAbstractProcessingParameterWidgetWrapper class
            # TODO QGIS 4.0 - remove
            if issubclass(wrapper.__class__, WidgetWrapper):
                w = wrapper.widget
            else:
                w = wrapper.wrappedWidget()

            self.connectWidgetChangedSignals(w)
            for c in w.findChildren(QWidget):
                self.connectWidgetChangedSignals(c)

        for output_widget in self.outputWidgets.values():
            self.connectWidgetChangedSignals(output_widget)

    def connectWidgetChangedSignals(self, w):
        if isinstance(w, QLineEdit):
            w.textChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QComboBox):
            w.currentIndexChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QgsProjectionSelectionWidget):
            w.crsChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, QCheckBox):
            w.stateChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, MultipleInputPanel):
            w.selectionChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, NumberInputPanel):
            w.hasChanged.connect(self.parametersHaveChanged)
        elif isinstance(w, DestinationSelectionPanel):
            w.destinationChanged.connect(self.parametersHaveChanged)

    def parametersHaveChanged(self):
        context = createContext()
        feedback = QgsProcessingFeedback()
        try:
            parameters = self.parent.getParameterValues()
            for output in self.alg.destinationParameterDefinitions():
                if not output.name() in parameters or parameters[output.name()] is None:
                    parameters[output.name()] = self.tr("[temporary file]")
            for p in self.alg.parameterDefinitions():
                if (not p.name() in parameters and not p.flags() & QgsProcessingParameterDefinition.FlagOptional) \
                        or (not p.checkValueIsAcceptable(parameters[p.name()])):
                    # not ready yet
                    self.text.setPlainText('')
                    return
            commands = self.alg.getConsoleCommands(parameters, context, feedback, executing=False)
            commands = [c for c in commands if c not in ['cmd.exe', '/C ']]
            self.text.setPlainText(" ".join(commands))
        except AlgorithmDialogBase.InvalidParameterValue as e:
            self.text.setPlainText(self.tr("Invalid value for parameter '{0}'").format(e.parameter.description()))
            if e.parameter.name()=='MAP_CSV':
                raise

class ChloeFieldsFromCSVWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return None
        else:
            return super().createLabel()

    def createWidget(self):
        """Widget creation to put like panel in dialog"""

        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return CSVFieldSelectionPanel(self.dialog, self.param.algorithm(), None)
        # BATCH AND MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText('Field 1;Field 2')
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget
       
    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        # BATCH AND MODELER GUI
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        # BATCH AND MODELER GUI
        else:
            return self.widget.text()

class ChloeValuesWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(self,input_asc='INPUT_ASC'):
        """Widget creation to put like panel in dialog"""
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return ValuesSelectionPanel(self.dialog, self.param.algorithm(), None, input_asc)
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return ValuesSelectionPanel(self.dialog, self.param.algorithm(), None, input_asc, True)
        # MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText('1;2;5')
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        # STANDARD AND BATCH GUI
        if self.dialogType == DIALOG_STANDARD or self.dialogType == DIALOG_BATCH:
            self.widget.setValue(str(value))
        # MODELER GUI
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        # STANDARD AND BATCH GUI
        if self.dialogType == DIALOG_STANDARD or self.dialogType == DIALOG_BATCH:
            return self.widget.getValue()
        # MODELER GUI
        else:
            return self.widget.text()

class ChloeClassificationTableWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return None
        else:
            return super().createLabel()

    def createWidget(self):
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            return ClassificationTablePanel(self.dialog, self.param.algorithm(), None)
        elif self.dialogType == DIALOG_BATCH:
            #todo
            return ClassificationTablePanel(self.dialog, self.param.algorithm(), None)
        else:
            #todo
            return ClassificationTablePanel(self.dialog, self.param.algorithm(), None)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            # todo
            self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()

class ChloeFactorTableWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return None
        else:
            return super().createLabel()

    def createWidget(self, input_matrix=None):
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            return FactorTablePanel(self.dialog, self.param.algorithm(), None, input_matrix)
        # BATCH AND MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText('Combination Formula')
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        # BATCH AND MODELER GUI
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        # BATCH AND MODELER GUI
        else:
            return self.widget.text()

class ChloeMappingTableWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(self, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        if self.dialogType == DIALOG_STANDARD:
            return TableReplaceInputPanel(self.dialog, self.param.algorithm(), None)
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return TableReplaceInputPanel(self.dialog, self.param.algorithm(), None, True)
        # MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText('(1,3);(2,9)')
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD or self.dialogType == DIALOG_BATCH:
            self.widget.setValue(str(value))
        # MODELER GUI
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD or self.dialogType == DIALOG_BATCH:
            return self.widget.getValue()
        # MODELER GUI
        else:
            return self.widget.text()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refreshMappingCombobox(self):
        print('updateMapAsc triggered')
        paramPanel = self.dialog.mainWidget()
        wrapper = paramPanel.wrappers[self.parentWidgetConfig['paramName']]
        widget = wrapper.widget
        mappingFilepath = widget.getValue()
        self.widget.updateMapCSV(mapFile=mappingFilepath)

    def refreshMappingAsc(self):
        print('updateMapAsc triggered')
        self.widget.updateMapASC()

class ChloeEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    
    def createWidget(self, dependantWidgetConfig=None):
        """  """
        self.dependantWidgetConfig = dependantWidgetConfig
        res = super().createWidget()
        return res

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(lambda x: self.updateDependantWidget(widgetWrapperList))
        self.updateDependantWidget(widgetWrapperList)
        
    def updateDependantWidget(self, wrapperList):
        for c in self.dependantWidgetConfig:
            dependantWrapperList = list(filter(lambda w: w.parameterDefinition().name()==c['paramName'], wrapperList))
            if len(dependantWrapperList)>0:
                dependantWrapper = dependantWrapperList[0]
                if isinstance(dependantWrapper,FileWidgetWrapper):
                    dependantWidget = dependantWrapper.widget
                else:
                    dependantWidget = dependantWrapper.wrappedWidget()
                dependantWidget.setEnabled(self.value()==c['enableValue'])

class ChloeMultiEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    """ same as ChloeEnumUpdateStateWidgetWrapper class but we can use different values of the same parameter to unlock another parameter """
    def createWidget(self, dependantWidgetConfig=None):
        """  """
        self.dependantWidgetConfig = dependantWidgetConfig
        res = super().createWidget()
        return res

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(lambda x: self.updateDependantWidget(widgetWrapperList))
        self.updateDependantWidget(widgetWrapperList)
        
    def updateDependantWidget(self, wrapperList):
        for c in self.dependantWidgetConfig:
            dependantWrapperList = list(filter(lambda w: w.parameterDefinition().name()==c['paramName'], wrapperList))
            if len(dependantWrapperList)>0:
                dependantWrapper = dependantWrapperList[0]
                if isinstance(dependantWrapper,FileWidgetWrapper):
                    dependantWidget = dependantWrapper.widget
                else:
                    dependantWidget = dependantWrapper.wrappedWidget()
                dependantWidget.setEnabled(str(self.value()) in c['enableValue'].split(','))

class ChloeDoubleComboboxWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(self, dictValues, initialValue, rasterLayerParamName, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return DoubleCmbBoxSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName)
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return DoubleCmbBoxSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName, False)
            # get raster values 
        # MODELER GUI
        else:
            return DoubleCmbBoxSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName, False)
            

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            # todo
            self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()
    
    def getParentWidgetConfig(self):
        return self.parentWidgetConfig
    
    def refreshMappingCombobox(self):
        self.widget.initCalculateMetric()
        self.widget.updateMetric()

class ChloeMultipleMetricsSelectorWidgetWrapper(WidgetWrapper):
    def createWidget(self, dictValues, initialValue, rasterLayerParamName, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        if self.dialogType == DIALOG_STANDARD:
            return ListSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName)
        elif self.dialogType == DIALOG_BATCH:
            #todo
            return ListSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName,False)
        else:
            #todo
            #return (self.dialog, self.param.algorithm(), None)
            return ListSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName,False)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            # todo
            pass
            #self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()
    
    def getParentWidgetConfig(self):
        return self.parentWidgetConfig
    
    def refreshMetrics(self):
        self.widget.update()

class ChloeAscRasterWidgetWrapper(RasterWidgetWrapper):
    
    def createWidget(self, dependantWidgetConfig=None):
        """  """
        res = super().createWidget()
        self.fileFilter = 'ASCII (*.asc)' + ';;' + self.tr('All files (*.*)')
        return res

    # overiding this method to redefine fileFilter 
    def getFileName(self, initial_value=''):
        """Shows a file open dialog"""
        settings = QgsSettings()
        if os.path.isdir(initial_value):
            path = initial_value
        elif os.path.isdir(os.path.dirname(initial_value)):
            path = os.path.dirname(initial_value)
        elif settings.contains('/Processing/LastInputPath'):
            path = str(settings.value('/Processing/LastInputPath'))
        else:
            path = ''

        filename, selected_filter = QFileDialog.getOpenFileName(self.widget, self.tr('Select File'),
                                                                path, self.fileFilter)
        if filename:
            settings.setValue('/Processing/LastInputPath',
                              os.path.dirname(str(filename)))
        return filename, selected_filter

    def postInitialize(self, widgetWrapperList):
        # no initial selection
        if self.dialogType == DIALOG_STANDARD:
            self.combo.setLayer(None)

class ChloeIntListWidgetWrapper(WidgetWrapper):
    
    def createWidget(self, initialValue, minValue, maxValue, oddNum=None):
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            return IntListSelectionPanel(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)
        elif self.dialogType == DIALOG_BATCH:
            return IntListSelectionPanel(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)
        else:
            #return (self.dialog, self.param.algorithm(), None)
            return IntListSelectionPanel(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            # todo
            pass
            #self.widget.setValue(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()

class ChloeIntSpinboxWrapper(WidgetWrapper):
    
    def createWidget(self, initialValue, minValue, maxValue, oddNum): 
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            return IntSpinbox(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)
        elif self.dialogType == DIALOG_BATCH:
            return IntSpinbox(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)
        else:
            #return (self.dialog, self.param.algorithm(), None)
            return IntSpinbox(self.dialog, self.param.algorithm(), initialValue, minValue, maxValue, oddNum)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(int(value))
        else:
            # todo
            self.widget.setValue(int(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.getValue()

class ChloeCsvTxtFileWidgetWrapper(FileWidgetWrapper):
    """ Overload of FileWidgetWrapper to adjust file filter """
    def createWidget(self, fileExtensions=[]):
        self.fileExtensions = fileExtensions
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            res = ChloeCsvTxtFileSelectionPanel(self.parameterDefinition().behavior() == QgsProcessingParameterFile.Folder,
                                      self.fileExtensions)
        else:
            res = super().createWidget()
        return res

    def selectFile(self):
        settings = QgsSettings()
        if os.path.isdir(os.path.dirname(self.combo.currentText())):
            path = os.path.dirname(self.combo.currentText())
        if settings.contains('/Processing/LastInputPath'):
            path = settings.value('/Processing/LastInputPath')
        else:
            path = ''

        if self.fileExtensions!=[]:
            listExtensions = list(map(lambda e : self.tr('{} files').format(e.upper()) + ' (*.' + e + ')', self.fileExtensions))
            listExtensions.append(self.tr('All files (*.*)'))
            filter = ';;'.join(listExtensions)
        else:
            filter = self.tr('All files (*.*)')
        filename, selected_filter = QFileDialog.getOpenFileName(self.widget,
                                                                self.tr('Select File'), path,
                                                                filter)
        if filename:
            self.combo.setEditText(filename)

class ChloeCsvTxtFileSelectionPanel(FileSelectionPanel):
    """ Overload of FileSelectionPanel to adjust file filter """
    def __init__(self, isFolder, extList=None):
        super().__init__(isFolder,None)
        self.extList = extList
    
    def showSelectionDialog(self):
        # Find the file dialog's working directory
        settings = QgsSettings()
        text = self.leText.text()
        if os.path.isdir(text):
            path = text
        elif os.path.isdir(os.path.dirname(text)):
            path = os.path.dirname(text)
        elif settings.contains('/Processing/LastInputPath'):
            path = settings.value('/Processing/LastInputPath')
        else:
            path = ''

        if self.isFolder:
            folder = QFileDialog.getExistingDirectory(self,
                                                      self.tr('Select Folder'), path)
            if folder:
                self.leText.setText(folder)
                settings.setValue('/Processing/LastInputPath',
                                  os.path.dirname(folder))
        else:
            listExtensions = list(map(lambda e : self.tr('{} files').format(e.upper()) + ' (*.' + e + ')', self.extList))
            listExtensions.append(self.tr('All files (*.*)'))
            fileFilter = ';;'.join(listExtensions)
            filenames, selected_filter = QFileDialog.getOpenFileNames(self,
                                                                      self.tr('Select File'), path, fileFilter)
            if filenames:
                self.leText.setText(u';'.join(filenames))
                settings.setValue('/Processing/LastInputPath',
                                  os.path.dirname(filenames[0]))

class ChloeCSVParameterFileDestination(QgsProcessingParameterFileDestination):
    def __init__(self, name, description, fileFilter='CSV (*.csv)', addToMapDefaultState=False):
        super().__init__(name=name, description=description, fileFilter=fileFilter)
        self.addToMapDefaultState = addToMapDefaultState
    
    def checkValueIsAcceptable(self, input, context = None):
        try:
            #STANDARD GUI RETURN
            return 'data' in input and super().checkValueIsAcceptable(input['data'], context)
        except:
            #BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context)

class ChloeASCParameterFileDestination(QgsProcessingParameterFileDestination):
    def __init__(self, name, description, fileFilter='ASC (*.asc)'):
        super().__init__(name=name, description=description, fileFilter=fileFilter)
    
    def checkValueIsAcceptable(self, input, context = None):
        try:
            #STANDARD GUI RETURN
            return 'data' in input and super().checkValueIsAcceptable(input['data'], context)
        except:
            #BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context)

class ChloeParameterFolderDestination(QgsProcessingParameterFolderDestination):
    def checkValueIsAcceptable(self, input, context = None):
        try:
            #STANDARD GUI RETURN
            return 'data' in input and super().checkValueIsAcceptable(input['data'], context)
        except:
            #BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context) 
