# -*- coding: utf-8 -*-

from builtins import str
from builtins import range
from builtins import object
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import (
    QDialog,
    QListView,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel

from random import randint


class DialListCheckBox(object):
    """
    Dialog with list check box
    example : 1,2,4,6,8
    """

    def __init__(self, values, checked_values=[]):
        self.dial = QDialog()
        self.result = ""

        # Layout Principal
        m_vbl = QVBoxLayout(self.dial)

        # List item checkable
        view = QListView()
        m_vbl.addWidget(view)

        self.m_sim = QStandardItemModel()
        view.setModel(self.m_sim)

        self._load_item(values, checked_values)

        # List buttons
        bt_all = QPushButton(self.tr("All"))
        bt_all.clicked.connect(lambda: self._check_all())

        bt_nothing = QPushButton(self.tr("Nothing"))
        bt_nothing.clicked.connect(lambda: self._check_nothing())

        bt_print = QPushButton(self.tr("Ok"))
        bt_print.clicked.connect(lambda: self._check_ok())

        # Sub layout for buttons
        m_vbh = QHBoxLayout()
        m_vbl.addLayout(m_vbh)

        m_vbh.addWidget(bt_all)
        m_vbh.addWidget(bt_nothing)
        m_vbh.addWidget(bt_print)

    def _load_item(self, values, checked_values):
        """Load item list"""
        for v in values:
            item = QStandardItem(str(v))
            if v in checked_values:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            self.m_sim.appendRow(item)

    def _check_all(self):
        """Check all item"""
        for index in range(
            self.m_sim.rowCount()
        ):  # Iteration sur le model (contient la list des items)
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Unchecked:  # Si Unchecked
                item.setCheckState(Qt.Checked)

    def _check_nothing(self):
        """Uncheck all item"""
        for index in range(
            self.m_sim.rowCount()
        ):  # Iteration sur le model (contient la list des items)
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Checked:  # Si Checked
                item.setCheckState(Qt.Unchecked)

    def _check_ok(self):
        """Get value of checked items and exit"""
        l_value = []
        # Iteration sur le model (contient la list des items)
        for index in range(self.m_sim.rowCount()):
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Checked:  # Si Checked
                l_value.append(str(item.text()))

        if l_value:
            s_value = ";".join(l_value)
        else:
            s_value = ""

        self.result = s_value
        self.dial.close()

    def run(self):
        self.dial.setWindowTitle(self.tr("Select values"))

        self.dial.exec_()
        return self.result

    def tr(self, string, context=""):
        if context == "" or context == None:
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)
