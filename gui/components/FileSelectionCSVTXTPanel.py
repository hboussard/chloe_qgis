# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
# 
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
# 
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################

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