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

import os

# import copy
import pathlib
from .helpers.dataclass import CombineFactorElement


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
    QgsApplication,
    QgsSettings,
    QgsProcessingFeedback,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameters,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFile,
    QgsProcessingException,
    QgsProcessingParameterFile,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterRasterLayer,
)

from qgis.gui import (
    QgsProjectionSelectionWidget,
    QgsProcessingLayerOutputDestinationWidget,
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

        for k in self.wrappers:
            w = self.wrappers[k]
            if hasattr(w, "getParentWidgetConfig"):
                config = w.getParentWidgetConfig()
                # print(config)
                if config is not None:
                    linked_params = config.get("linkedParams", [])
                    for linked_param in linked_params:
                        p = self.wrappers[linked_param["paramName"]]
                        m = getattr(w, linked_param["refreshMethod"])
                        if m is not None:
                            widget = (
                                p.widget
                                if issubclass(p.__class__, WidgetWrapper)
                                else p.wrappedWidget()
                            )
                            # print(type(widget))
                            # add here widget signal connections
                            if isinstance(widget, FileSelectionPanel):
                                widget.leText.textChanged.connect(m)
                            elif isinstance(p, RasterWidgetWrapper):
                                p.combo.valueChanged.connect(m)
                            elif isinstance(p, MultipleInputPanel):
                                p.selectionChanged.connect(m)
                                try:
                                    widget.selectionChanged.connect(m)
                                except:
                                    print("an error occured cant get selectionChanged")

                        else:
                            continue

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

        try:
            # messy as all heck, but we don't want to call the dialog's implementation of
            # createProcessingParameters as we want to catch the exceptions raised by the
            # parameter panel instead...
            parameters = (
                {}
                if self.dialog.mainWidget() is None
                else self.dialog.mainWidget().createProcessingParameters()
            )
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

            try:
                commands = self.algorithm().getConsoleCommands(
                    parameters, context, feedback, executing=False
                )
                commands = [c for c in commands if c not in ["cmd.exe", "/C "]]
                self.text.setPlainText(" ".join(commands))
            except QgsProcessingException as e:
                self.text.setPlainText(str(e))
        except AlgorithmDialogBase.InvalidParameterValue as e:
            self.text.setPlainText(
                self.tr("Invalid value for parameter '{0}'").format(
                    e.parameter.description()
                )
            )
        except AlgorithmDialogBase.InvalidOutputExtension as e:
            self.text.setPlainText(e.message)


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
            # if isinstance(layout, (QVBoxLayout)):
            #     if layout.objectName() == target_layout_name:
            #         layout.insertWidget(position, widget)
            widget = QLineEdit()  # QgsPanelWidget()
            # widget.setPlaceholderText("1;2;5")
            # if self.parameterDefinition().defaultValue():
            #     widget.setText(self.parameterDefinition().defaultValue())
            return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        # STANDARD AND BATCH GUI
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            self.widget.setValue(str(value))
        else:
            self.widget.setText(str(value))
        # MODELER GUI
        # else:
        #     pass
        # self.widget.setText(str(value))
        # if self.parameterDefinition().multiLine():
        #     self.widget.setValue(value)
        # else:
        #     self.setComboValue(value)

    def value(self):
        """Get value on the widget/component."""
        # STANDARD AND BATCH GUI
        if self.dialogType in (DIALOG_STANDARD, DIALOG_BATCH):
            return self.widget.getValue()
        else:
            return self.widget.text()
        # MODELER GUI
        # else:
        #     pass
        # return self.widget.text()

        # if self.parameterDefinition().multiLine():
        #     value = self.widget.getValue()
        #     option = self.widget.getOption()
        #     if option == MultilineTextPanel.USE_TEXT:
        #         if value == "":
        #             if (
        #                 self.parameterDefinition().flags()
        #                 & QgsProcessingParameterDefinition.FlagOptional
        #             ):
        #                 return None
        #             else:
        #                 raise InvalidParameterValue()
        #         else:
        #             return value
        #     else:
        #         return value
        # else:

        #     def validator(v):
        #         return (
        #             bool(v)
        #             or self.parameterDefinition().flags()
        #             & QgsProcessingParameterDefinition.FlagOptional
        #         )

        #     return self.comboValue(validator)


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
    def createWidget(self, input_matrix=None, parentWidgetConfig=None):
        """Widget creation to put like panel in dialog"""
        self.parentWidgetConfig = parentWidgetConfig
        return FactorTablePanel(
            self.dialog, self.param.algorithm(), None, input_matrix, self.dialogType
        )

    def setValue(self, value: "list[list[CombineFactorElement] |str]"):
        """Set value on the widget/component."""

        if value is None:
            return
        self.widget.setValue(value)

    def value(self):
        """Get value on the widget/component."""
        return self.widget.value()

    def getParentWidgetConfig(self):
        return self.parentWidgetConfig

    def resetFormula(self):
        self.widget.resetFormula()

    def refreshFactorTable(self):
        self.widget.populateTableModel()


class ChloeMappingTableWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return super().createLabel()
        else:  # ?????
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

        if self.parentWidgetConfig:
            for param in self.parentWidgetConfig["linkedParams"]:
                if param["paramName"] == "MAP_CSV":
                    wrapper = paramPanel.wrappers[param["paramName"]]
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
        if self.dependantWidgetConfig:
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
        if self.dependantWidgetConfig:
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
        elif self.dialogType in (DIALOG_BATCH, DIALOG_MODELER):
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
        # else:
        #     widget = QLineEdit()
        #     widget.setPlaceholderText("")
        #     if self.parameterDefinition().defaultValue():
        #         widget.setText(self.parameterDefinition().defaultValue())
        #     return widget

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None:
            return
        if self.dialogType == DIALOG_STANDARD:
            self.widget.setValue(str(value))
        else:
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
    def __init__(self, name, description):
        super().__init__(name, description)

    def defaultFileExtension(self):
        return "csv"

    def createFileFilter(self):
        return "{} (*.csv *.CSV)".format(
            QCoreApplication.translate("ChloeAlgorithm", "CSV files")
        )

    # def checkValueIsAcceptable(self, input, context=None):
    #     try:
    #         # STANDARD GUI RETURN
    #         return "data" in input and super().checkValueIsAcceptable(
    #             input["data"], context
    #         )
    #     except:
    #         # BATCH AND MODERLER GUI RETURN
    #         return input and super().checkValueIsAcceptable(input, context)


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

    # def checkValueIsAcceptable(self, input, context=None):
    #     # print(input)
    #     try:
    #         # print(
    #         #     "data" in input
    #         #     and super().checkValueIsAcceptable(input["data"], context)
    #         # )
    #         # print("data" in input)
    #         # STANDARD GUI RETURN
    #         # return "data" in input and super().checkValueIsAcceptable(
    #         #     input["data"], context
    #         # )
    #         return True
    #     except:
    #         # BATCH AND MODERLER GUI RETURN
    #         # data = input.sink.value(QgsExpressionContext())[0]
    #         return input and super().checkValueIsAcceptable(input, context)
    #         # return super().checkValueIsAcceptable(data, context)


class ChloeParameterFolderDestination(QgsProcessingParameterFolderDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def clone(self):
        copy = ChloeParameterFolderDestination(self.name(), self.description())
        return copy

    # def checkValueIsAcceptable(self, input, context=None):
    #     try:
    #         # STANDARD GUI RETURN
    #         return "data" in input and super().checkValueIsAcceptable(
    #             input["data"], context
    #         )
    #     except:
    #         # BATCH AND MODERLER GUI RETURN
    #         return input and super().checkValueIsAcceptable(input, context)
