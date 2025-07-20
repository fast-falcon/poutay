"""Sample action showing usage."""

from action.base import ActionBase

class ExampleActions(ActionBase):
    def on_button_clicked(self, ui):
        print("Button clicked", ui)
