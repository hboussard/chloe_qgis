# coding: utf-8

from qgis.PyQt.QtCore import pyqtSignal
from processing.gui.InputLayerSelectorPanel import InputLayerSelectorPanel
from processing.core.parameters import ParameterRaster

class CustomInputLayerSelectorPanel(InputLayerSelectorPanel):
    """
    This class add a signal of the class InputLayerSelectorPanel
    With this, we can change/synchronize the QWidget 'QComboBox' 
    with the alg.param a.k.a INPUT_LAYER
    """
    currentIndexChanged = pyqtSignal()
    
    def __init__(self, options, param):
        """constructor"""
        super(CustomInputLayerSelectorPanel, self).__init__(options, param)

        # Connection of QComboBox signal with this signal 
        self.cmbText.currentIndexChanged.connect(lambda: self.currentIndexChanged.emit())
        



