from PySide6.QtCore import QObject

from .baresip import Transport, Protocol, Manager, Config, Process


class Worker(QObject):

    def __init__(self):
        super().__init__()

        self.config = Config()
        args = ["-f", self.config.config_file]

        self.exec = Process(arguments=args, parent=self)
        self.t = Transport(host="127.0.0.1", port=4444, parent=self)
        self.p = Protocol(self.t, parent=self)
        self.manager = Manager(self.p, parent=self)
