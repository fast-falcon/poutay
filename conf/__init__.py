class Lazy_setting():
    def __getattr__(self, item):
        pass
    def __setattr__(self, key, value):
        pass
    def load(self):
        pass

settings = Lazy_setting()