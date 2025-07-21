"""Sample UI class."""

from poutay.views.ui_class import UIMain
from poutay.action.main import MainActions

class SampleWindow(UIMain, metaclass=type(UIMain)):
    widget_file = "ui_files/sample.ui"
    actions_cls = MainActions
