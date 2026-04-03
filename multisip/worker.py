from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from .baresip import Transport, Protocol, Manager, create_config, Process
from .user_agent import UserAgent, user_agent_password_from_user
from .config import Config
from .log import get_logger


class Worker(QObject):

    userAgentAdded = Signal(UserAgent, int)  # ua, index

    def __init__(self, config: Config, tmpdir: Path):
        super().__init__()

        self._log = get_logger(self.__class__.__name__)
        self._log.debug("worker started")

        self.config = config

        create_config(tmpdir)
        args = ["-f", str(tmpdir)]

        self.process = Process(arguments=args, parent=self)
        self.process.start()

        self.t = Transport(host="127.0.0.1", port=4444, parent=self)
        self.t.connect()

        self.p = Protocol(self.t, parent=self)
        self.manager = Manager(self.p, parent=self)

        self._connect_signals()

        self._ua_indexes = {}

    def _connect_signals(self):
        self.manager.userAgentCreated.connect(self._handle_ua_added)

    def add_uas(self, start_account_number: int, count: int) -> None:
        prev_uas_count = len(self.manager.user_agents())
        added_uas_count = 0
        self._ua_indexes.clear()

        for i in range(count):
            user = start_account_number + i
            password = user_agent_password_from_user(user)
            ua = self.manager.add_user_agent(user, password, self.config.domain)
            if ua is None:
                continue
            self.manager.create_user_agent(ua)
            self._ua_indexes[ua] = prev_uas_count + added_uas_count
            added_uas_count += 1

    def _handle_ua_added(self, ua: UserAgent):
        self.userAgentAdded.emit(ua, self._ua_indexes[ua])

    @Slot()
    def stop(self):
        self.process.stop()
        self.process.waitForFinished(10000)
