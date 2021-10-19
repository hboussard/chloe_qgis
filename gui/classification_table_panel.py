# -*- coding: utf-8 -*-

"""
***************************************************************************
    ClassificationTablePanel.py
    ---------------------
    Date                 : August 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = 'Jean-Charles Naud'
__date__ = 'August 2017'
__copyright__ = '(C) 2017, Jean-Charles Naud'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic
from qgis.core import QgsApplication
from .components.TableInputDialog import TableInputDialog
import math

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python', 'plugins', 'processing', 'ui', 'widgetBaseSelector.ui'))


class ClassificationTablePanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None):
        super(ClassificationTablePanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('Domain1, class1;Domain2, class2')

        self.btnSelect.clicked.connect(self.selectValues)  # Bouton "..."

    def selectValues(self):
        """Values selector
            return item (duck typing)
        """
        # Get initial value
        text = self.leText.text()
        values = ""

        # Dialog list check box
        dial = TableInputDialog(self.tr("Fill the class mapping table"))
        result = dial.run(text)

        # result
        if result:
            self.leText.setText(result)

    def getValue(self):
        return unicode(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass
