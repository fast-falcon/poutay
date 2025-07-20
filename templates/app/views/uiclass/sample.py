"""Sample UI class."""

from views.ui_class import UIMain
from action.main import MainActions

class SampleWindow(UIMain, metaclass=type(UIMain)):
    widget_file = "ui_files/sample.ui"
    actions_cls = MainActions
