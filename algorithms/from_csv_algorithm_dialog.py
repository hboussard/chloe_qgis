# -*- coding: utf-8 -*-

"""
***************************************************************************
    from_csv_algorithm_dialog.py
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

from processing.gui.wrappers import WidgetWrapper

from qgis.PyQt.QtWidgets import (QPushButton)
from qgis.PyQt.QtWidgets import QFileDialog

from ..gui.csv_field_selection_panel import CSVFieldSelectionPanel

from ..chloe_algorithm_dialog import ChloeAlgorithmDialog, ChloeParametersPanel
from ..ChloeUtils import *

from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER, DIALOG_BATCH, DIALOG_STANDARD


class FromCSVAlgorithmDialog(ChloeAlgorithmDialog):

    def __init__(self, alg):
        super().__init__(alg)

    def getParametersPanel(self, alg, parent):
        return FromCSVParametersPanel(parent, alg)


class FromCSVParametersPanel(ChloeParametersPanel):

    def __init__(self, parent, alg):

        self.dialog = parent

        super().__init__(parent, alg)

    def initWidgets(self):

        super().initWidgets()

        # Add and plug the "Import header" button in dialog
        self.pb = QPushButton(self.tr("Import header"))

        self.pbHeader = self.pb
        self.pbHeader.clicked.connect(self.uploadHeader)

        # insert extra pb
        ChloeUtils.insertWidgetInLayout(
            parent=self.dialog, target_layout_name='mScrollAreaLayout', widget=self.pb, position=3)

    def uploadHeader(self):
        """Import header from ASCII or TXT file.

        This function open a QFileDialog() to select and open an ASC file.
        The beginning of this file (ie. the header) is parsed to get value and
        to fill corresponding widget parameter value.
        The goal is to automate the filling of the parameters to improve
        the user experience

        Example of file header:
        ```
        ncols 144
        nrows 138
        xllcorner 312487.6891250734
        yllcorner 2397321.4964859663
        cellsize 10.0
        NODATA_value -1
        ```
        """

        # Select the file with a QFileDialog()
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # dlg.setFilter("ASC File (*.asc);; TXT File (*.txt);;All File (*.*)")
        dlg.setNameFilters(
            ["All File (*.*)", "ASC File (*.asc)", "TXT File (*.txt)"])
        dlg.selectNameFilter("All File (*.*)")
        filenames = ''
        if dlg.exec_():
            filenames = dlg.selectedFiles()
        if filenames != '':
            # Open the file and parse header data
            with open(str(filenames[0]), 'r') as infile:
                for line in infile:
                    values = line.strip().split(' ')
                    if values[0] == "ncols":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["N_COLS"], int(values[1]))
                    elif values[0] == "nrows":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["N_ROWS"], float(values[1]))
                    elif values[0] == "xllcorner":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["XLL_CORNER"], float(values[1]))
                    elif values[0] == "yllcorner":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["YLL_CORNER"], float(values[1]))
                    elif values[0] == "cellsize":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["CELL_SIZE"], float(values[1]))
                    elif values[0] == "NODATA_value":
                        ChloeUtils.wrapperSetValue(
                            self.wrappers["NODATA_VALUE"], int(values[1]))
                    else:
                        break


class ChloeFieldsWidgetWrapper(WidgetWrapper):
    def createLabel(self):
        """Label create"""
        if self.dialogType == DIALOG_STANDARD:
            return None
        else:
            return super().createLabel()

    def createWidget(self):
        """Widget creation to put like panel in dialog"""
        if self.dialogType == DIALOG_STANDARD:
            # return CSVFieldSelectionPanel(self.dialog, self.param.algorithm(), None)
            return CSVFieldSelectionPanel(self.dialog, self.param.algorithm(), None)
        elif self.dialogType == DIALOG_BATCH:
            # todo
            return None
        else:
            # todo
            return CSVFieldSelectionPanel(self.dialog, self.param.algorithm(), None)

    def setValue(self, value):
        """Set value on the widget/component."""
        if value is None or value == NULL:
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
