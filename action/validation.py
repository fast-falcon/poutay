from PySide6.QtWidgets import QWidget


class ValidationBase:
    """Base class providing data validation for actions."""

    def __init__(self):
        self.cleaned_data = {}

    def collect_inputs(self, ui):
        """Gather values from child widgets of ``ui.widget``."""
        data = {}
        for child in ui.widget.findChildren(QWidget):
            name = child.objectName()
            if not name:
                continue
            if hasattr(child, "text") and callable(child.text):
                try:
                    data[name] = child.text()
                    continue
                except Exception:
                    pass
            if hasattr(child, "currentText") and callable(child.currentText):
                try:
                    data[name] = child.currentText()
                    continue
                except Exception:
                    pass
            if hasattr(child, "isChecked") and callable(child.isChecked):
                try:
                    data[name] = child.isChecked()
                    continue
                except Exception:
                    pass
            if hasattr(child, "value") and callable(child.value):
                try:
                    data[name] = child.value()
                    continue
                except Exception:
                    pass
        return data

    def is_valid(self, action_name, ui):
        """Run validation for an action handler."""
        self.cleaned_data = self.collect_inputs(ui)
        method = getattr(self, f"valid_{action_name}", None)
        if callable(method):
            result = method(self.cleaned_data, ui)
            if result is False:
                return False
            if isinstance(result, dict):
                self.cleaned_data.update(result)
        clean = getattr(self, "clean", None)
        if callable(clean):
            result = clean(self.cleaned_data, ui)
            if result is False:
                return False
            if isinstance(result, dict):
                self.cleaned_data.update(result)
        return True
