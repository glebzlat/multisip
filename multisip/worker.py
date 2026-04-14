import time

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

    workerReady = Signal()

    def __init__(self, config: Config, tmpdir: Path) -> None:
        super().__init__()

        self._log = get_logger(self.__class__.__name__)

        self._tmpdir = tmpdir

        self.config = config

        create_config(tmpdir)

        self._ua_indexes = {}
        self._unmuted_ua: Optional[UserAgent] = None
        self._pending_unmute_ua: Optional[UserAgent] = None

        args = ["-f", str(self._tmpdir)]
        self.process = Process(arguments=args, parent=self)

        self.t = Transport(host="127.0.0.1", port=4444, parent=self)
        self.p = Protocol(self.t, parent=self)
        self.manager = Manager(self.p, parent=self)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.process.started.connect(self._handle_process_started)

        self.t.connectedChanged.connect(self._handle_transport_connected)

        self.manager.userAgentCreated.connect(self._handle_ua_added)
        self.manager.incomingCall.connect(self._handle_incoming_call)
        self.manager.callEstablished.connect(self._handle_call_established)
        self.manager.callClosed.connect(self._handle_call_closed)
        self.manager.userAgentDeleted.connect(self._handle_ua_deleted)
        self.manager.transactionCompletedSimple.connect(self._handle_transaction_completed)

    @Slot()
    def start(self) -> None:
        self.process.start()

    @Slot()
    def stop(self) -> None:
        self.process.stop()

    @Slot()
    def set_running(self, running: bool) -> None:
        if running is True and not self.process.is_running():
            self.process.start()
        else:
            self.process.stop()

    @Slot(int, int)
    def add_uas(self, start_account_number: int, count: int) -> None:
        prev_uas_count = len(self.manager.user_agents())
        added_uas_count = 0

        for i in range(count):
            user = start_account_number + i
            password = user_agent_password_from_user(user)
            ua = self.manager.add_user_agent(user, password, self.config.domain)
            if ua is None:
                continue
            self.manager.create_user_agent(ua)
            self._ua_indexes[ua] = prev_uas_count + added_uas_count
            added_uas_count += 1

    @Slot()
    def handle_delete_all(self) -> None:
        for ua in reversed(self.manager.user_agents()):
            self.manager.delete_user_agent(ua)

    @Slot()
    def handle_mute_all(self) -> None:
        self._pending_unmute_ua = None
        self._unmuted_ua = None
        for ua in self.manager.user_agents():
            self._set_mute(ua, True)

    @Slot()
    def handle_hangup_all(self) -> None:
        self.manager.hangup_all()

    @Slot(UserAgent)
    def handle_delete_ua(self, ua: UserAgent) -> None:
        self.manager.delete_user_agent(ua)

    @Slot(UserAgent)
    def handle_hangup_call(self, ua: UserAgent) -> None:
        self.manager.hangup(ua)

    @Slot(UserAgent, bool)
    def handle_set_mute(self, ua: UserAgent, value: bool) -> None:
        self._set_mute(ua, value)

    @Slot(int)
    def _handle_process_started(self, pid: int) -> None:
        time.sleep(0.1)
        self.t.connect()

    @Slot(bool)
    def _handle_transport_connected(self, connected: bool) -> None:
        if not connected:
            return

        self._log.debug("worker components initialized")
        self._log.debug("config is stored in %s", self._tmpdir)

        for ua in self.manager.user_agents():
            self.manager.create_user_agent(ua)

        self.workerReady.emit()

    @Slot(UserAgent, dict)
    def _handle_ua_added(self, ua: UserAgent) -> None:
        index = self._ua_indexes.get(ua)
        if index is None:
            # Handle the case when the process was stopped with UAs added.
            # We are re-creating UAs in-place, so they have no indexes here.
            return
        del self._ua_indexes[ua]
        self.userAgentAdded.emit(ua, index)

    @Slot(UserAgent, Event)
    def _handle_incoming_call(self, ua: UserAgent, ev: Event) -> None:
        self._log.info("incoming call: to %d from %s", ua.user, ev.contact_uri)
        self.manager.accept(ua)

    @Slot(UserAgent, Event)
    def _handle_call_established(self, ua: UserAgent, ev: Event) -> None:
        self.manager.hold(ua)

    @Slot(UserAgent, Event)
    def _handle_call_closed(self, ua: UserAgent, ev: Event) -> None:
        self._log.info("call closed: to %d from %s", ua.user, ev.contact_uri)
        if self._unmuted_ua == ua:
            self._unmuted_ua = None
        if self._pending_unmute_ua == ua:
            self._pending_unmute_ua = None
        self.muteStateChanged.emit(ua, True)

    @Slot(UserAgent, dict)
    def _handle_ua_deleted(self, ua: UserAgent) -> None:
        if self._unmuted_ua == ua:
            self._unmuted_ua = None
        if self._pending_unmute_ua == ua:
            self._pending_unmute_ua = None
        self.manager.remove_user_agent(ua)

    @Slot(ProtocolOperation, UserAgent)
    def _handle_transaction_completed(self, op: ProtocolOperation, ua: UserAgent) -> None:
        if op == ProtocolOperation.HOLD:
            if self._unmuted_ua == ua:
                self._unmuted_ua = None
            self.muteStateChanged.emit(ua, True)
        elif op == ProtocolOperation.RESUME:
            self._pending_unmute_ua = None
            self._unmuted_ua = ua
            self.muteStateChanged.emit(ua, False)

    @Slot(UserAgent, bool)
    def _set_mute(self, ua: UserAgent, value: bool) -> None:
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
