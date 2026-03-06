import logging

from dataclasses import dataclass
from typing import Optional, Callable

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

from .user_agent import UserAgent, Status as UserAgentStatus, user_agent_password_from_user
from .baresip import BareSIP


class WorkerInputMessage:
    pass


class WorkerOutputMessage:
    pass


@dataclass(frozen=True)
class AddUAsRequest(WorkerInputMessage):
    start_number: int
    count: int
    domain: str


@dataclass(frozen=True)
class AddUAItemMessage(WorkerOutputMessage):
    user_agent: UserAgent
    index: int
    append_index: int
    error: Optional[str] = None


@dataclass(frozen=True)
class AddUAFinishedMessage(WorkerOutputMessage):
    pass


@dataclass(frozen=True)
class GetUAStatusRequest(WorkerInputMessage):
    user_agent: UserAgent


@dataclass(frozen=True)
class GetUAStatusResponse(WorkerOutputMessage):
    user_agent: UserAgent
    status: UserAgentStatus


@dataclass(frozen=True)
class UAChangedStatusMessage(WorkerOutputMessage):
    user_agent: UserAgent
    status: UserAgentStatus


def handle(event: type):

    def handle_decorator(meth):
        meth._expected_event = event
        return meth

    return handle_decorator


@dataclass
class UserAgentState:
    baresip: BareSIP
    status: UserAgentStatus


class Worker(QObject):

    sendMessage = pyqtSignal(WorkerOutputMessage)

    _handlers: dict[WorkerInputMessage, Callable] = {}

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        super().__init__(obj)
        for mem_name in dir(cls):
            mem = getattr(obj, mem_name)
            if (expected_event := getattr(mem, "_expected_event", None)) is not None:
                assert callable(mem)
                obj._handlers[expected_event] = mem
        return obj

    def __init__(self, ):
        super().__init__()

        self._timer: Optional[QTimer] = None
        self._message: Optional[WorkerInputMessage] = None

        self._user_agents: dict[UserAgent, UserAgentState] = {}
        self._user_agents_iter = None

    @pyqtSlot()
    def start(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self.poll)
        self._timer.start(100)

    @pyqtSlot()
    def stop(self):
        self._timer.stop()
        for _, state in self._user_agents.items():
            state.baresip.stop()

    def poll(self):
        if self._message:
            handler = self._handlers[self._message.__class__]
            for resp in handler(self._message):
                self.sendMessage.emit(resp)
            self._message = None

        else:
            if self._user_agents_iter is None:
                self._user_agents_iter = iter(self._user_agents.items())
            try:
                ua, state = next(self._user_agents_iter)
            except (RuntimeError, StopIteration):
                self._user_agents_iter = iter(self._user_agents.items())
                return
            new_status = state.baresip.get_user_agent_status()
            if new_status != state.status:
                self.sendMessage.emit(UAChangedStatusMessage(ua, new_status))
                state.status = new_status

    @pyqtSlot(WorkerInputMessage)
    def receive_message(self, message):
        self._message = message

    @handle(AddUAsRequest)
    def _handle_add_uas(self, message: AddUAsRequest):
        prev_len = len(self._user_agents.keys())

        for i in range(message.count):
            user = message.start_number + i
            ua = UserAgent(
                user=user,
                domain=message.domain,
                password=user_agent_password_from_user(user)
            )

            instance = BareSIP(ua, log_level=logging.DEBUG)
            instance.start()
            status = instance.create_user_agent()

            self._user_agents[ua] = UserAgentState(
                baresip=instance,
                status=status
            )

            resp = AddUAItemMessage(
                user_agent=ua,
                index=i,
                append_index=prev_len + i,
            )
            yield resp

        yield AddUAFinishedMessage()

    @handle(GetUAStatusRequest)
    def _handle_get_status(self, message: GetUAStatusRequest):
        status = self._user_agents[message.user_agent].status
        yield GetUAStatusResponse(user_agent=message.user_agent, status=status)
