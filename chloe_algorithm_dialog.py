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

__author__ = "Jean-Charles Naud/Alkante"
__date__ = "May 2015"
__copyright__ = "(C) 2015, Victor Olaya"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from functools import partial
from pprint import pformat
import time
import os
import warnings

# import copy
import pathlib


from qgis.utils import iface

from qgis.PyQt.QtCore import QCoreApplication, QCoreApplication, Qt
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QFileDialog,
)

from qgis.core import (
    QgsProject,
    QgsApplication,
    QgsSettings,
    QgsProcessingFeedback,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameters,
    QgsProcessingParameterVectorDestination,
    QgsProcessingOutputLayerDefinition,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFile,
    QgsExpressionContext,
    QgsProcessingParameterExtent,
    QgsProcessingModelAlgorithm,
)

from qgis.gui import (
    QgsProjectionSelectionWidget,
    QgsProcessingLayerOutputDestinationWidget,
    QgsProcessingHiddenWidgetWrapper,
    QgsProcessingParameterWidgetContext,
    QgsGui,
    QgsProcessingGui,
)

from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.gui.NumberInputPanel import NumberInputPanel

from processing.gui.FileSelectionPanel import FileSelectionPanel
from processing.gui.wrappers import (
    WidgetWrapper,
    EnumWidgetWrapper,
    WidgetWrapperFactory,
)
from processing.tools.dataobjects import createContext

from processing.gui.ParametersPanel import ParametersPanel

from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase

from .ChloePostProcessing import ChloehandleAlgorithmResults

from processing.gui.wrappers import (
    WidgetWrapper,
    RasterWidgetWrapper,
    FileWidgetWrapper,
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)

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
    QgsApplication.pkgDataPath(), "python", "plugins", "processing"
)


class ChloeAlgorithmDialog(AlgorithmDialog):
    def __init__(self, alg, parent=None):
        super().__init__(alg, parent=parent)
        self.mainWidget().parametersHaveChanged()

    def getParametersPanel(self, alg, parent):
        return ChloeParametersPanel(parent, alg)


class ChloeParametersPanel(ParametersPanel):
    def __init__(self, parent, alg):

        super().__init__(parent, alg)

        self.dialog = parent

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
        self.addExtraWidget(w)

        # self.pbHeader = pb
        self.connectParameterSignals()
        self.parametersHaveChanged()

    def initWidgets(self):  # heavy overload

        super().initWidgets()

        # if isinstance(
        #     output,
        #     (
        #         ChloeCSVParameterFileDestination,
        #         ChloeASCParameterFileDestination,
        #         ChloeParameterFolderDestination,
        #     ),
        # ):
        #     if hasattr(output, "addToMapDefaultState"):
        #         for w in widget.children():
        #             if isinstance(w, QCheckBox):
        #                 w.setChecked(output.addToMapDefaultState)

        for k in self.wrappers:
            w = self.wrappers[k]
            if hasattr(w, "getParentWidgetConfig"):
                # print(str(w) + " "  + "getParentWidgetConfig")
                config = w.getParentWidgetConfig()
                if config is not None:

                    # LINKED PARAMETER ONE
                    p = self.wrappers[config["paramName"]]
                    m = getattr(w, config["refreshMethod"])

                    if m is not None:

                        widget = p.wrappedWidget()
                        # todo generalize valueChanged handling
                        # to any type of widget componant
                        if isinstance(widget, FileSelectionPanel):
                            widget.leText.textChanged.connect(m)
                        elif isinstance(p, RasterWidgetWrapper):
                            try:
                                p.combo.valueChanged.connect(m)  # QGIS 3.8 version
                            except:
                                p.combo.currentIndexChanged.connect(m)  # QGIS LTR 3.4
                        elif isinstance(widget, MultipleInputPanel):
                            try:
                                widget.selectionChanged.connect(m)
                            except:
                                pass
                                # p.combo.currentIndexChanged.connect(m)

                        # LINKED PARAMETER TWO
                        try:
                            p2 = self.wrappers[config["paramName2"]]
                            m2 = getattr(w, config["refreshMethod2"])

                            widget2 = p2.wrappedWidget()
                            if isinstance(widget2, FileSelectionPanel):
                                widget2.leText.textChanged.connect(m2)

                            elif isinstance(p2, RasterWidgetWrapper):
                                try:
                                    p2.combo.valueChanged.connect(
                                        m2
                                    )  # QGIS 3.8 version
                                except:
                                    p2.combo.currentIndexChanged.connect(
                                        m2
                                    )  # QGIS LTR 3.4
                        except:
                            pass

    def createProcessingParameters(self):
        parameters = {}
        for p, v in self.extra_parameters.items():
            parameters[p] = v

        for param in self.algorithm().parameterDefinitions():
            # print(param)

            if param.flags() & QgsProcessingParameterDefinition.FlagHidden:
                continue
            if not param.isDestination():
                try:
                    wrapper = self.wrappers[param.name()]
                except KeyError:
                    continue

                # For compatibility with 3.x API, we need to check whether the wrapper is
                # the deprecated WidgetWrapper class. If not, it's the newer
                # QgsAbstractProcessingParameterWidgetWrapper class
                # TODO QGIS 4.0 - remove
                if issubclass(wrapper.__class__, WidgetWrapper):
                    widget = wrapper.widget
                else:
                    widget = wrapper.wrappedWidget()

                if (
                    not isinstance(wrapper, QgsProcessingHiddenWidgetWrapper)
                    and widget is None
                ):
                    continue

                value = wrapper.parameterValue()
                parameters[param.name()] = value

                if not param.checkValueIsAcceptable(value):
                    raise AlgorithmDialogBase.InvalidParameterValue(param, widget)
            else:
                if self.in_place and param.name() == "OUTPUT":
                    parameters[param.name()] = "memory:"
                    continue

                try:
                    wrapper = self.wrappers[param.name()]
                except KeyError:
                    continue

                widget = wrapper.wrappedWidget()
                value = wrapper.parameterValue()

                dest_project = None

                if wrapper.customProperties().get("OPEN_AFTER_RUNNING"):

                    dest_project = QgsProject.instance()

                if value and isinstance(value, QgsProcessingOutputLayerDefinition):
                    value.destinationProject = dest_project
                if value:
                    parameters[param.name()] = value

                    context = createContext()
                    ok, error = param.isSupportedOutputValue(value, context)
                    if not ok:
                        raise AlgorithmDialogBase.InvalidOutputExtension(widget, error)

                # print(f'param : {param} , value : {value}')
                # if isinstance(param, (ChloeCSVParameterFileDestination, ChloeASCParameterFileDestination, ChloeParameterFolderDestination)):
                #     if hasattr(param, "addToMapDefaultState"):
                #         for w in widget.children():
                #             if isinstance(w, QCheckBox):
                #                 w.setChecked(param.addToMapDefaultState)

                if isinstance(
                    param,
                    (
                        ChloeCSVParameterFileDestination,
                        ChloeASCParameterFileDestination,
                        ChloeParameterFolderDestination,
                    ),
                ):

                    paramName = param.name()

                    if paramName in parameters:
                        p = parameters[paramName]

                        toBeOpened = wrapper.customProperties().get(
                            "OPEN_AFTER_RUNNING"
                        )
                        print(f"param : {param}, topbeopn : {toBeOpened}")
                        temporary_value_test = None

                        # get temporary value test from value.sink in case of QgsProcessingParameterRasterDestination/QgsProcessingParameterVectorDestination
                        if type(value) == QgsProcessingOutputLayerDefinition:
                            temporary_value_test = value.sink.value(
                                QgsExpressionContext()
                            )[0]

                        if (
                            temporary_value_test == "TEMPORARY_OUTPUT"
                            or value == "TEMPORARY_OUTPUT"
                        ):

                            dataValue = param.generateTemporaryDestination()

                        else:
                            if temporary_value_test:
                                dataValue = value.sink.value(QgsExpressionContext())[0]
                            else:
                                # if QgsProcessingParameterFolderDestination don't use the sink value
                                dataValue = value

                        newValue = {"data": dataValue, "openLayer": toBeOpened}
                        parameters[paramName] = newValue

                if param.name() == "SAVE_PROPERTIES":
                    if widget is not None:
                        if value == "TEMPORARY_OUTPUT":
                            newValue = param.generateTemporaryDestination()
                            parameters["SAVE_PROPERTIES"] = newValue

        return self.algorithm().preprocessParameters(parameters)

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
        elif isinstance(w, QgsProcessingLayerOutputDestinationWidget):
            w.destinationChanged.connect(self.parametersHaveChanged)

    def parametersHaveChanged(self):

        context = createContext()
        feedback = QgsProcessingFeedback()

        for output in self.algorithm().destinationParameterDefinitions():

            if isinstance(
                output,
                (ChloeCSVParameterFileDestination, ChloeASCParameterFileDestination),
            ):

                try:
                    wrapper = self.wrappers[output.name()]
                except KeyError:
                    continue

                widget = wrapper.wrappedWidget()

                if hasattr(output, "addToMapDefaultState"):
                    for w in widget.children():
                        if isinstance(w, QCheckBox):
                            if w.checkState():
                                w.setChecked(output.addToMapDefaultState)

        try:
            parameters = self.dialog.createProcessingParameters()
            for output in self.algorithm().destinationParameterDefinitions():
                if not output.name() in parameters or parameters[output.name()] is None:
                    if (
                        not output.flags()
                        & QgsProcessingParameterDefinition.FlagOptional
                    ):
                        parameters[output.name()] = self.tr("[temporary file]")

            for p in self.algorithm().parameterDefinitions():
                if p.flags() & QgsProcessingParameterDefinition.FlagHidden:
                    continue

                if (
                    p.flags() & QgsProcessingParameterDefinition.FlagOptional
                    and p.name() not in parameters
                ):
                    continue

                if p.name() not in parameters or not p.checkValueIsAcceptable(
                    parameters[p.name()]
                ):
                    # not ready yet
                    self.text.setPlainText("")
                    return

            commands = self.algorithm().getConsoleCommands(
                parameters, context, feedback, executing=False
            )
            # print(f'commands {commands}')
            commands = [c for c in commands if c not in ["cmd.exe", "/C "]]
            self.text.setPlainText(" ".join(commands))
        except AlgorithmDialogBase.InvalidParameterValue as e:
            # print(f'except {e}')
            self.text.setPlainText(
                self.tr("Invalid value for parameter '{0}'").format(
                    e.parameter.description()
                )
            )
            if e.parameter.name() == "MAP_CSV":
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
            widget.setPlaceholderText("Field 1;Field 2")
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

    def createWidget(self, input_asc="INPUT_ASC"):
        """Widget creation to put like panel in dialog"""
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return ValuesSelectionPanel(
                self.dialog, self.param.algorithm(), None, input_asc
            )
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return ValuesSelectionPanel(
                self.dialog, self.param.algorithm(), None, input_asc, True
            )
        # MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText("1;2;5")
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
            # todo
            return ClassificationTablePanel(self.dialog, self.param.algorithm(), None)
        else:
            # todo
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

    def createWidget(self, input_matrix=None, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        if self.dialogType == DIALOG_STANDARD:
            return FactorTablePanel(
                self.dialog, self.param.algorithm(), None, input_matrix
            )
        # BATCH AND MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText("Combination Formula")
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

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def resetFormula(self):
        self.widget.resetFormula()


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
            return TableReplaceInputPanel(
                self.dialog, self.param.algorithm(), None, True
            )
        # MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText("(1,3);(2,9)")
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

        paramPanel = self.dialog.mainWidget()
        wrapper = paramPanel.wrappers[self.parentWidgetConfig["paramName"]]
        widget = wrapper.widget
        mappingFilepath = widget.getValue()
        self.widget.updateMapCSV(mapFile=mappingFilepath)

    def refreshMappingAsc(self):
        self.widget.updateMapASC()

    def emptyMappingAsc(self):
        self.widget.emptyMappingAsc()


class ChloeEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    def createWidget(self, dependantWidgetConfig=None):
        """ """
        self.dependantWidgetConfig = dependantWidgetConfig
        res = super().createWidget()
        return res

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(
            lambda x: self.updateDependantWidget(widgetWrapperList)
        )
        self.updateDependantWidget(widgetWrapperList)

    def updateDependantWidget(self, wrapperList):
        for c in self.dependantWidgetConfig:
            dependantWrapperList = list(
                filter(
                    lambda w: w.parameterDefinition().name() == c["paramName"],
                    wrapperList,
                )
            )
            if len(dependantWrapperList) > 0:
                dependantWrapper = dependantWrapperList[0]
                if isinstance(dependantWrapper, FileWidgetWrapper):
                    dependantWidget = dependantWrapper.widget
                else:
                    dependantWidget = dependantWrapper.wrappedWidget()
                dependantWidget.setEnabled(self.value() == c["enableValue"])


class ChloeMultiEnumUpdateStateWidgetWrapper(EnumWidgetWrapper):
    """same as ChloeEnumUpdateStateWidgetWrapper class but we can use different values of the same parameter to unlock another parameter"""

    def createWidget(self, dependantWidgetConfig=None):
        """ """
        self.dependantWidgetConfig = dependantWidgetConfig
        res = super().createWidget()
        return res

    def postInitialize(self, widgetWrapperList):
        self.widget.currentIndexChanged.connect(
            lambda x: self.updateDependantWidget(widgetWrapperList)
        )
        self.updateDependantWidget(widgetWrapperList)

    def updateDependantWidget(self, wrapperList):
        for c in self.dependantWidgetConfig:
            dependantWrapperList = list(
                filter(
                    lambda w: w.parameterDefinition().name() == c["paramName"],
                    wrapperList,
                )
            )
            if len(dependantWrapperList) > 0:
                dependantWrapper = dependantWrapperList[0]
                if isinstance(dependantWrapper, FileWidgetWrapper):
                    dependantWidget = dependantWrapper.widget
                else:
                    dependantWidget = dependantWrapper.wrappedWidget()
                dependantWidget.setEnabled(
                    str(self.value()) in c["enableValue"].split(",")
                )


class ChloeDoubleComboboxWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:
            return super().createLabel()

    def createWidget(
        self, dictValues, initialValue, rasterLayerParamName, parentWidgetConfig=None
    ):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        # STANDARD GUI
        if self.dialogType == DIALOG_STANDARD:
            return DoubleCmbBoxSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
            )
        # BATCH GUI
        elif self.dialogType == DIALOG_BATCH:
            return DoubleCmbBoxSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
                False,
            )
            # get raster values
        # MODELER GUI
        else:
            widget = QLineEdit()
            widget.setPlaceholderText("")
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.text()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refreshMappingCombobox(self):
        self.widget.initCalculateMetric()
        self.widget.updateMetric()


class ChloeMultipleMetricsSelectorWidgetWrapper(WidgetWrapper):
    def createWidget(
        self, dictValues, initialValue, rasterLayerParamName, parentWidgetConfig=None
    ):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        if self.dialogType == DIALOG_STANDARD:
            return ListSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
            )
        elif self.dialogType == DIALOG_BATCH:
            return ListSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                dictValues,
                initialValue,
                rasterLayerParamName,
                False,
            )
        else:
            widget = QLineEdit()
            widget.setPlaceholderText("")
            if self.parameterDefinition().defaultValue():
                widget.setText(self.parameterDefinition().defaultValue())
            return widget

            # return ListSelectionPanel(self.dialog, self.param.algorithm(), dictValues, initialValue, rasterLayerParamName,False)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            self.widget.setText(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_STANDARD:
            return self.widget.getValue()
        else:
            return self.widget.text()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def refreshMetrics(self):
        self.widget.update()


class ChloeAscRasterWidgetWrapper(RasterWidgetWrapper):
    def createWidget(self, dependantWidgetConfig=None):
        """ """
        res = super().createWidget()
        self.fileFilter = "ASCII (*.asc)" + ";;" + self.tr("All files (*.*)")
        return res

    # overiding this method to redefine fileFilter
    def getFileName(self, initial_value=""):
        """Shows a file open dialog"""
        settings = QgsSettings()
        if os.path.isdir(initial_value):
            path = initial_value
        elif os.path.isdir(os.path.dirname(initial_value)):
            path = os.path.dirname(initial_value)
        elif settings.contains("/Processing/LastInputPath"):
            path = str(settings.value("/Processing/LastInputPath"))
        else:
            path = ""

        filename, selected_filter = QFileDialog.getOpenFileName(
            self.widget, self.tr("Select File"), path, self.fileFilter
        )
        if filename:
            settings.setValue(
                "/Processing/LastInputPath", os.path.dirname(str(filename))
            )
        return filename, selected_filter

    def postInitialize(self, widgetWrapperList):
        # no initial selection
        if self.dialogType == DIALOG_STANDARD:
            self.combo.setLayer(None)


class ChloeIntListWidgetWrapper(WidgetWrapper):
    def createWidget(self, initialValue, minValue, maxValue, oddNum=None):
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            return IntListSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )
        elif self.dialogType == DIALOG_BATCH:
            return IntListSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )
        else:
            # return (self.dialog, self.param.algorithm(), None)
            return IntListSelectionPanel(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
            # todo
            pass
            # self.widget.setValue(str(value))

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
            return IntSpinbox(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )
        elif self.dialogType == DIALOG_BATCH:
            return IntSpinbox(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )
        else:
            # return (self.dialog, self.param.algorithm(), None)
            return IntSpinbox(
                self.dialog,
                self.param.algorithm(),
                initialValue,
                minValue,
                maxValue,
                oddNum,
            )

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
    """Overload of FileWidgetWrapper to adjust file filter"""

    def createWidget(self, fileExtensions=[]):
        self.fileExtensions = fileExtensions
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            res = ChloeCsvTxtFileSelectionPanel(
                self.parameterDefinition().behavior()
                == QgsProcessingParameterFile.Folder,
                self.fileExtensions,
            )
        else:
            res = super().createWidget()
        return res

    def selectFile(self):
        settings = QgsSettings()
        if os.path.isdir(os.path.dirname(self.combo.currentText())):
            path = os.path.dirname(self.combo.currentText())
        if settings.contains("/Processing/LastInputPath"):
            path = settings.value("/Processing/LastInputPath")
        else:
            path = ""

        if self.fileExtensions != []:
            listExtensions = list(
                map(
                    lambda e: self.tr("{} files").format(e.upper()) + " (*." + e + ")",
                    self.fileExtensions,
                )
            )
            listExtensions.append(self.tr("All files (*.*)"))
            filter = ";;".join(listExtensions)
        else:
            filter = self.tr("All files (*.*)")
        filename, selected_filter = QFileDialog.getOpenFileName(
            self.widget, self.tr("Select File"), path, filter
        )
        if filename:
            self.combo.setEditText(filename)


class ChloeCsvTxtFileSelectionPanel(FileSelectionPanel):
    """Overload of FileSelectionPanel to adjust file filter"""

    def __init__(self, isFolder, extList=None):
        super().__init__(isFolder, None)
        self.extList = extList

    def showSelectionDialog(self):
        # Find the file dialog's working directory
        settings = QgsSettings()
        text = self.leText.text()
        if os.path.isdir(text):
            path = text
        elif os.path.isdir(os.path.dirname(text)):
            path = os.path.dirname(text)
        elif settings.contains("/Processing/LastInputPath"):
            path = settings.value("/Processing/LastInputPath")
        else:
            path = ""

        if self.isFolder:
            folder = QFileDialog.getExistingDirectory(
                self, self.tr("Select Folder"), path
            )
            if folder:
                self.leText.setText(folder)
                settings.setValue("/Processing/LastInputPath", os.path.dirname(folder))
        else:
            listExtensions = list(
                map(
                    lambda e: self.tr("{} files").format(e.upper()) + " (*." + e + ")",
                    self.extList,
                )
            )
            listExtensions.append(self.tr("All files (*.*)"))
            fileFilter = ";;".join(listExtensions)
            filenames, selected_filter = QFileDialog.getOpenFileNames(
                self, self.tr("Select File"), path, fileFilter
            )
            if filenames:
                self.leText.setText(";".join(filenames))
                settings.setValue(
                    "/Processing/LastInputPath", os.path.dirname(filenames[0])
                )


class ChloeCSVParameterFileDestination(QgsProcessingParameterVectorDestination):
    # def __init__(self, name, description, fileFilter='CSV (*.csv)', addToMapDefaultState=False):
    # super().__init__(name=name, description=description, fileFilter=fileFilter)

    def __init__(self, name, description, addToMapDefaultState=False):
        super().__init__(name, description)

        self.addToMapDefaultState = addToMapDefaultState

    def defaultFileExtension(self):
        return "csv"

    def createFileFilter(self):
        return "{} (*.csv *.CSV)".format(
            QCoreApplication.translate("ChloeAlgorithm", "CSV files")
        )

    def checkValueIsAcceptable(self, input, context=None):
        try:
            # STANDARD GUI RETURN
            return "data" in input and super().checkValueIsAcceptable(
                input["data"], context
            )
        except:
            # BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context)


class ChloeASCParameterFileDestination(QgsProcessingParameterRasterDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def clone(self):
        copy = ChloeASCParameterFileDestination(self.name(), self.description())
        return copy

    def defaultFileExtension(self):
        return "asc"

    def createFileFilter(self):
        return "{} (*.asc *.ASC)".format(
            QCoreApplication.translate("ChloeAlgorithm", "ASC files")
        )

    def supportedOutputRasterLayerExtensions(self):
        return ["asc"]

    def parameterAsOutputLayer(self, definition, value, context):
        return super(
            QgsProcessingParameterRasterDestination, self
        ).parameterAsOutputLayer(definition, value, context)

    def isSupportedOutputValue(self, value, context):
        output_path = QgsProcessingParameters.parameterAsOutputLayer(
            self, value, context
        )
        if pathlib.Path(output_path).suffix.lower() != ".asc":
            return False, QCoreApplication.translate(
                "ChloeAlgorithm", "Output filename must use a .asc extension"
            )
        return True, ""

    def checkValueIsAcceptable(self, input, context=None):
        try:
            # STANDARD GUI RETURN
            return "data" in input and super().checkValueIsAcceptable(
                input["data"], context
            )
        except:
            # BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context)


class ChloeParameterFolderDestination(QgsProcessingParameterFolderDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def clone(self):
        copy = ChloeParameterFolderDestination(self.name(), self.description())
        return copy

    def checkValueIsAcceptable(self, input, context=None):
        try:
            # STANDARD GUI RETURN
            return "data" in input and super().checkValueIsAcceptable(
                input["data"], context
            )
        except:
            # BATCH AND MODERLER GUI RETURN
            return input and super().checkValueIsAcceptable(input, context)
