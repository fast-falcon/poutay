class ActionMeta(type):
    """Collects action handlers defined on subclasses.

    Methods following the ``on_<widget>_<signal>`` naming pattern are
    automatically registered as handlers. These methods should accept
    ``self`` (the action object) and ``ui`` (an instance of the ``UIMain``
    subclass) as their parameters.
    """

    def __new__(cls, name, bases, attrs):
        actions = {}
        for base in bases:
            actions.update(getattr(base, "actions", {}))

        # Auto detect methods following the ``on_<widget>_<signal>`` pattern
        for attr_name, attr_value in list(attrs.items()):
            if (
                callable(attr_value)
                and attr_name.startswith("on_")
                and "_" in attr_name[3:]
            ):
                widget, event = attr_name[3:].rsplit("_", 1)
                actions[widget] = (event, attr_value)

        actions.update(attrs.get("actions", {}))
        attrs["actions"] = actions
        return super().__new__(cls, name, bases, attrs)


class ActionBase(metaclass=ActionMeta):
    """Base class for defining UI actions.

    Subclasses provide methods such as ``on_button_clicked`` which will be
    invoked with ``self`` (the action instance) and ``ui`` (the UI instance).
    """

    actions = {}
