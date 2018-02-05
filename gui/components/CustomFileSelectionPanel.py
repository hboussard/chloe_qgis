# coding: utf-8

from qgis.PyQt.QtCore import pyqtSignal
from processing.gui.FileSelectionPanel import FileSelectionPanel


class CustomFileSelectionPanel(FileSelectionPanel):
    """
    This class add a signal of the class FileSelectionPanel
    With this, we can change/synchronize the QWidget 'QLineEdit' 
    with the alg.param a.k.a INPUT_FILE_*
    """
    textChanged = pyqtSignal()
    
    def __init__(self, isFolder, ext=None):
        """constructor"""
        super(CustomFileSelectionPanel, self).__init__(isFolder, ext)

        # Connection of QLineEdit signal with this signal 
        self.leText.textChanged.connect(lambda: self.textChanged.emit())



