import sys
import types
import logging
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from core.signals import MetaSignals
from settings import FONT_PATH, QSS_PATH
from action.base import ActionBase
import assets_rc


class Storage(dict):
    """Dictionary subclass enabling attribute access."""

    def __getattribute__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class UIMainMeta(type):
    """Metaclass that loads UI files and wires up signals."""

    storage_instance = Storage()
    wins = []

    def __new__(cls, cls_name, bases, attrs):
        logging.info("Creating class: %s", cls_name)
        new_cls = super().__new__(cls, cls_name, bases, attrs)
        new_cls.app = QApplication.instance() or QApplication(sys.argv)
        logging.info("QApplication instance initialized.")

        if cls_name == "UIMain" and not bases:
            logging.info("Skipping UI loading for base class: %s", cls_name)
            return new_cls

        loader = QUiLoader()
        ui_file = QFile(str(new_cls.widget_file))
        if not ui_file.open(QFile.ReadOnly):
            logging.error("Failed to open UI file: %s", new_cls.widget_file)
        else:
            logging.info("UI file opened: %s", new_cls.widget_file)
        new_cls.widget = loader.load(ui_file)
        ui_file.close()
        logging.info("UI loaded and file closed.")

        new_cls.widget.meta_signals = MetaSignals(new_cls.widget)
        logging.info("MetaSignals attached to widget.")

        new_cls.actions_cls = attrs.get("actions_cls", ActionBase)
        new_cls.action_instance = new_cls.actions_cls()

        for name, (in_event, in_func) in new_cls.actions_cls.actions.items():
            logging.info(
                "Connecting action: widget='%s', event='%s', handler='%s'",
                name,
                in_event,
                in_func.__name__,
            )
            wid = getattr(new_cls.widget, name)
            event = getattr(wid, in_event)
            method = UIMainMeta.create_connection_method(in_func, new_cls.action_instance)
            bound_method = types.MethodType(method, new_cls)
            setattr(new_cls, f"func_{name}_{in_event}_handler", bound_method)
            event.connect(getattr(new_cls, f"func_{name}_{in_event}_handler"))
            logging.info("Action connected: %s.%s", name, in_event)

        for name, ui_file in new_cls.sub_widget_files.items():
            ui_file_q = QFile(str(ui_file))
            if not ui_file_q.open(QFile.ReadOnly):
                logging.error("Failed to open UI file: %s", name)
            else:
                logging.info("UI file opened: %s", name)
            setattr(new_cls, name, loader.load(ui_file_q))
            ui_file_q.close()

        logging.info("Class %s created successfully.", cls_name)
        new_cls.storage = cls.storage_instance
        new_cls._instance = None

        @classmethod
        def instance(cls, *a, **kw):
            if cls._instance is None:
                cls._instance = cls(*a, **kw)
                cls._instance.widget.hide()
            return cls._instance

        new_cls.instance = instance

        @classmethod
        def show(cls):
            for cl in cls.wins:
                cl.hide()
            cls.instance().widget.show()

        @classmethod
        def hide(cls):
            if cls._instance:
                cls._instance.widget.hide()

        new_cls.show = show
        new_cls.hide = hide
        cls.wins.append(new_cls)
        return new_cls

    @staticmethod
    def create_connection_method(func, action_instance):
        def wrap(cls):
            logging.info("Executing action handler: %s", func.__name__)
            ui = cls.instance()
            valid = True
            if hasattr(action_instance, "validate"):
                valid = action_instance.validate(func.__name__, ui)
            if valid:
                getattr(action_instance, func.__name__)(ui)

        return wrap


class UIMain(metaclass=UIMainMeta):
    """Base class that handles theme and font loading."""

    widget_file = None
    actions_cls = ActionBase
    sub_widget_files = {}

    def __init__(self):
        self.app = type(self).app
        self.widget = type(self).widget

        from PySide6.QtCore import QTextStream

        file = QFile(QSS_PATH)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            qss = stream.readAll()
            self.app.setStyleSheet(qss)
            file.close()
        else:
            print("\u274c Failed to open resource file")

        if self.widget is None or not isinstance(self.widget, QWidget):
            print("[-] Failed to load QWidget.")
            sys.exit(-1)

        self.setup()

    def setup(self):
        self.set_font(FONT_PATH, size=12)

    def run(self):
        sys.exit(self.app.exec())
