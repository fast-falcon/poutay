import logging
from .base import ActionBase


class MainActions(ActionBase):
    """Concrete actions for the main UI window."""

    def on_toolButton_password_display_mode_clicked(self, ui):
        logging.info("Password display mode toggled")

    def on_pushButton_login_via_sms_clicked(self, ui):
        logging.info("Login via SMS selected")

    def on_pushButton_login_via_password_clicked(self, ui):
        logging.info("Login via password selected")

    def on_pushButton_reset_password_clicked(self, ui):
        logging.info("Change mobile number/reset password")

    def on_pushButton_resend_sms_clicked(self, ui):
        logging.info("Resend SMS clicked")

    def on_pushButton_submit_clicked(self, ui):
        logging.info("Submit clicked")

