from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from .baresip import (
    Transport,
    Protocol,
    Manager,
    create_config,
    Process,
    Event,
    Operation as ProtocolOperation,
)
from .user_agent import UserAgent, Status as RegStatus, user_agent_password_from_user
from .config import Config
from .log import get_logger


class Worker(QObject):

    userAgentAdded = Signal(UserAgent, int)  # ua, index
    userAgentDeleted = Signal(UserAgent)
    muteStateChanged = Signal(UserAgent, bool)  # ua, muted

    def __init__(self, config: Config, tmpdir: Path):
        super().__init__()

        self._log = get_logger(self.__class__.__name__)

        self.config = config

        create_config(tmpdir)

        args = ["-f", str(tmpdir)]
        self.process = Process(arguments=args, parent=self)

        self.t = Transport(host="127.0.0.1", port=4444, parent=self)
        self.p = Protocol(self.t, parent=self)
        self.manager = Manager(self.p, parent=self)

        self._ua_indexes = {}
        self._unmuted_ua: Optional[UserAgent] = None
        self._pending_unmute_ua: Optional[UserAgent] = None

        self._connect_signals()

    def _connect_signals(self):
        self.process.started.connect(self._handle_process_started)

        self.t.connectedChanged.connect(self._handle_transport_connected)

        self.manager.userAgentCreated.connect(self._handle_ua_added)
        self.manager.incomingCall.connect(self._handle_incoming_call)
        self.manager.callEstablished.connect(self._handle_call_established)
        self.manager.callClosed.connect(self._handle_call_closed)
        self.manager.userAgentDeleted.connect(self._handle_ua_deleted)
        self.manager.transactionCompletedSimple.connect(self._handle_transaction_completed)

    @Slot()
    def start(self):
        self.process.start()

    @Slot()
    def stop(self):
        self.process.stop()

    @Slot()
    def set_running(self, running: bool):
        if running is True and not self.process.is_running():
            self.process.start()
        else:
            self.process.stop()

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

    def handle_delete_all(self):
        for ua in reversed(self.manager.user_agents()):
            self.manager.delete_user_agent(ua)

    def handle_mute_all(self):
        self._pending_unmute_ua = None
        self._unmuted_ua = None
        for ua in self.manager.user_agents():
            self._set_mute(ua, True)

    def handle_hangup_all(self):
        self.manager.hangup_all()

    def handle_delete_ua(self, ua: UserAgent):
        self.manager.delete_user_agent(ua)

    def handle_hangup_call(self, ua: UserAgent):
        self.manager.hangup(ua)

    @Slot(UserAgent, bool)
    def handle_set_mute(self, ua: UserAgent, value: bool):
        self._set_mute(ua, value)

    def _handle_process_started(self, pid: int):
        self.t.connect()

    def _handle_transport_connected(self, connected: bool):
        if connected:
            self._log.debug("worker components initialized")

    def _handle_ua_added(self, ua: UserAgent):
        self.userAgentAdded.emit(ua, self._ua_indexes[ua])

    def _handle_incoming_call(self, ua: UserAgent, ev: Event):
        self._log.info("incoming call: to %d from %s", ua.user, ev.contact_uri)
        self.manager.accept(ua)

    def _handle_call_established(self, ua: UserAgent, ev: Event):
        self.manager.hold(ua)

    def _handle_call_closed(self, ua: UserAgent, ev: Event):
        self._log.info("call closed: to %d from %s", ua.user, ev.contact_uri)
        if self._unmuted_ua == ua:
            self._unmuted_ua = None
        if self._pending_unmute_ua == ua:
            self._pending_unmute_ua = None
        self.muteStateChanged.emit(ua, True)

    def _handle_ua_deleted(self, ua: UserAgent):
        if self._unmuted_ua == ua:
            self._unmuted_ua = None
        if self._pending_unmute_ua == ua:
            self._pending_unmute_ua = None
        self.manager.remove_user_agent(ua)

    def _handle_transaction_completed(self, op: ProtocolOperation, ua: UserAgent):
        if op == ProtocolOperation.HOLD:
            if self._unmuted_ua == ua:
                self._unmuted_ua = None
            self.muteStateChanged.emit(ua, True)
        elif op == ProtocolOperation.RESUME:
            self._pending_unmute_ua = None
            self._unmuted_ua = ua
            self.muteStateChanged.emit(ua, False)

    def _set_mute(self, ua: UserAgent, value: bool):
        if value:
            self._log.info("muting ua: %s", ua)
            if self._pending_unmute_ua == ua:
                self._pending_unmute_ua = None
            if self._unmuted_ua == ua:
                self._unmuted_ua = None
            self.manager.hold(ua)
        else:
            if self._unmuted_ua is not None and self._unmuted_ua != ua:
                self._log.info("muting another ua: %s", self._unmuted_ua)
                self.manager.hold(self._unmuted_ua)
            self._log.info("unmuting ua: %s", ua)
            self._pending_unmute_ua = ua
            self.manager.resume(ua)
