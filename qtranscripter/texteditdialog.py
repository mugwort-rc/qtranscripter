# -*- coding: utf-8 -*-

from PyQt4.Qt import *

from ui_texteditdialog import Ui_TextEditDialog

class TextEditDialog(QDialog):
    def __init__(self, parent):
        """
        :type parent: QObject
        """
        super(TextEditDialog, self).__init__(parent)
        self.ui = Ui_TextEditDialog()
        self.ui.setupUi(self)

    def setText(self, text):
        """
        :type text: str
        """
        self.ui.plainTextEdit.setPlainText(text)

    def text(self):
        """
        :rtype: str
        """
        return self.ui.plainTextEdit.toPlainText()
