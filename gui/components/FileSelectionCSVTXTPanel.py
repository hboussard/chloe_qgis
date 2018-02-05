# -*- coding: utf-8 -*-

"""
***************************************************************************
    NumberInputDialog.py
    ---------------------
    Date                 : January 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""
__author__ = 'Jean-Charles Naud'
__date__ = 'January 2017'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QSettings

from processing.tools.system import isWindows
from processing.gui.FileSelectionPanel import FileSelectionPanel



class FileSelectionCSVTXTPanel(FileSelectionPanel):
  def showSelectionDialog(self):
    # Find the file dialog's working directory
    settings = QSettings()
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
                                                  self.tr('Select folder'), path)
        if folder:
            self.leText.setText(folder)
            settings.setValue('/Processing/LastInputPath',
                              os.path.dirname(folder))
    else:
        filenames = QFileDialog.getOpenFileNames(self,
                                                  self.tr('Select file'), path, "CSV (*.csv);;TXT (*.txt);;All (*.*)")
        if filenames:
            self.leText.setText(u';'.join(filenames))
            settings.setValue('/Processing/LastInputPath',
                              os.path.dirname(filenames[0]))