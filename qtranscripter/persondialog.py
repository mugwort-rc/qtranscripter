# -*- coding: utf-8 -*-

import six

from PyQt4.Qt import *

from ui_persondialog import Ui_PersonDialog
from texteditdialog import TextEditDialog

class PersonDialog(QDialog):
    def __init__(self, parent):
        """
        :type parent: QObject
        """
        super(PersonDialog, self).__init__(parent)
        self.ui = Ui_PersonDialog()
        self.ui.setupUi(self)

        self.current = QModelIndex()
        self.model = QStringListModel(self)
        self.ui.listView.setModel(self.model)

    def person(self):
        if not self.current.isValid():
            return ""
        return six.text_type(self.current.data().toPyObject())

    @pyqtSlot()
    def on_toolButton_clicked(self):
        text = "\n".join(self.model.stringList())
        view = TextEditDialog(self)
        view.setText(text)
        if view.exec_() != QDialog.Accepted:
            return
        text = six.text_type(view.text())
        self.model.setStringList(text.strip().split("\n"))

    @pyqtSlot()
    def on_lineEdit_returnPressed(self):
        text = six.text_type(self.ui.lineEdit.text())
        text = text.lower()
        try:
            row = int(text)
            row -= 1
            assert row >= 0 and row < len(self.model.stringList())
            self.current = self.model.index(row, 0)
            self.ui.lineEdit.clear()
            self.accept()
        except:
            pass

    @pyqtSlot(QModelIndex)
    def on_listView_doubleClicked(self, index):
        self.current = index
        self.accept()
