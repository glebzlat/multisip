from __future__ import annotations

import logging
import dataclasses

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal

from .protocol import CtrlTcpProtocol
from ..user_agent import UserAgent, Status as RegStatus
from ..log import get_logger


class Operation(StrEnum):
    CREATE_UA = "create_ua"
    DELETE_UA = "delete_ua"
    REQUEST_REGINFO = "request_reginfo"
    DIAL = "dial"
    MUTE = "mute"
    RESUME = "resume"
    ACCEPT = "accept"
    HANGUP = "hangup"
    HANGUP_ALL = "hangup_all"
    CALLSTAT = "callstat"
    CALLFIND = "callfind"


@dataclass(slots=True, frozen=True)
class Event:
    type: Optional[str]
    aor: Optional[str]
    call_id: Optional[str]
    peer_uri: Optional[str]
    param: Optional[str]
    contact_uri: Optional[str]
    user: Optional[str]


class CtrlTcpManager(QObject):

    @dataclass(slots=True)
    class PendingRequest:
        token: str
        operation: Operation
        ua: Optional[UserAgent] = None
        params: Optional[str] = None
        meta: dict[str, Any] = field(default_factory=dict)
        transaction_id: Optional[str] = None

    @dataclass(slots=True)
    class UserAgentState:
        ua: UserAgent
        aor: str
        created: bool = False
        reg_status: RegStatus = RegStatus.PENDING
        current_call_id: Optional[str] = None
        current_call_line: Optional[int] = None
        last_event: Optional[str] = None

    @dataclass(slots=True)
    class TransactionStep:
        operation: Operation
        ua: Optional[UserAgent]
        params: Optional[str]
        sender: Callable[[str], None]  # sender(token)

    @dataclass(slots=True)
    class Transaction:
        id: str
        final_operation: Operation
        ua: Optional[UserAgent]
        steps: list[CtrlTcpManager.TransactionStep]
        index: int = 0
        responses: list[dict[str, Any]] = field(default_factory=list)

        @property
        def finished(self) -> bool:
            return self.index >= len(self.steps)

        def current_step(self) -> Optional[CtrlTcpManager.TransactionStep]:
            if self.finished:
                return None
            return self.steps[self.index]

    # Raw correlated lifecycle
    requestSent = Signal(PendingRequest)                  # PendingRequest
    requestFinished = Signal(PendingRequest, dict)        # PendingRequest, response
    requestTimedOut = Signal(PendingRequest)              # PendingRequest
    unknownResponse = Signal(dict)

    # Transaction lifecycle
    transactionStarted = Signal(Transaction)           # Transaction
    transactionStepFinished = Signal(Transaction, dict)  # Transaction, response
    transactionCompleted = Signal(Transaction)         # Transaction
    transactionFailed = Signal(Transaction, dict)      # Transaction, failed_response

    transactionCompletedSimple = Signal(Operation, UserAgent)

    # UA lifecycle
    userAgentAdded = Signal(UserAgent)               # UserAgent
    userAgentRemoved = Signal(UserAgent)             # UserAgent
    userAgentCreated = Signal(UserAgent, dict)       # UserAgent, response
    userAgentDeleted = Signal(UserAgent, dict)       # UserAgent, response
    userAgentRegistrationChanged = Signal(UserAgent, RegStatus)  # UserAgent, RegStatus

    # Call events
    incomingCall = Signal(UserAgent, Event)
    callEstablished = Signal(UserAgent, Event)
    callClosed = Signal(UserAgent, Event)

    # Raw protocol passthrough
    eventReceived = Signal(dict)
    messageReceived = Signal(dict)

    # Errors
    managerError = Signal(str)

    def __init__(self, protocol: CtrlTcpProtocol, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._p = protocol

        self._pending_requests: dict[str, CtrlTcpManager.PendingRequest] = {}
        self._sequence_by_key: dict[str, int] = {}

        self._user_agents: dict[UserAgent, CtrlTcpManager.UserAgentState] = {}
        self._ua_by_aor: dict[str, CtrlTcpManager.UserAgentState] = {}

        self._transactions: dict[str, CtrlTcpManager.Transaction] = {}
        self._transaction_queue: deque[str] = deque()
        self._active_transaction_id: Optional[str] = None
        self._transaction_seq: int = 0

        self._p.responseReceived.connect(self._on_response)
        self._p.eventReceived.connect(self._on_event)
        self._p.messageReceived.connect(self._on_message)

        self.managerError.connect(self._on_error)
        self.requestSent.connect(self._on_request_sent)

        self._log = get_logger(self.__class__.__name__)

    # -------------------------------------------------------------------------
    # Public inspection API
    # -------------------------------------------------------------------------

    def user_agents(self) -> list[UserAgent]:
        return list(self._user_agents.keys())

    def pending_request(self, token: str) -> Optional[PendingRequest]:
        return self._pending_requests.get(token)

    def pending_requests(self) -> list[PendingRequest]:
        return list(self._pending_requests.values())

    # -------------------------------------------------------------------------
    # Public UA API
    # -------------------------------------------------------------------------

    def add_user_agent(self, user: int, password: str, domain: str) -> Optional[UserAgent]:
        ua = UserAgent(user=user, password=password, domain=domain)
        aor = self._aor_of(ua)

        if aor in self._ua_by_aor:
            self.managerError.emit(f"user agent already added: {aor}")
            return None

        state = self.UserAgentState(ua=ua, aor=aor)
        self._user_agents[ua] = state
        self._ua_by_aor[aor] = state
        self.userAgentAdded.emit(ua)
        return ua

    def remove_user_agent(self, ua: UserAgent) -> bool:
        state = self._user_agents.get(ua)
        if state is None:
            self.managerError.emit(f"user agent not found: {ua}")
            return False

        if state.created:
            self.managerError.emit(f"user agent still exists in baresip: {ua}")
            return False

        del self._user_agents[ua]
        self._ua_by_aor.pop(state.aor, None)
        self._sequence_by_key.pop(state.aor, None)
        self.userAgentRemoved.emit(ua)
        return True

    def create_user_agent(self, ua: UserAgent) -> None:
        state = self._ensure_known_ua(ua)
        acc_line = self._account_line_of(ua)

        self._send_request(
            operation=Operation.CREATE_UA,
            ua=ua,
            params=acc_line,
            sender=lambda token: self._call_protocol("uanew", acc_line, token=token),
        )

    def delete_user_agent(self, ua: UserAgent) -> None:
        state = self._ensure_known_ua(ua)

        self._send_request(
            operation=Operation.DELETE_UA,
            ua=ua,
            params=state.aor,
            sender=lambda token: self._call_protocol("uadel", state.aor, token=token),
        )

    def request_reginfo(self) -> None:
        self._send_request(
            operation=Operation.REQUEST_REGINFO,
            sender=lambda token: self._call_protocol("reginfo", token=token),
        )

    def dial(self, ua: UserAgent, uri: str) -> None:
        self._ensure_known_ua(ua)

        self._send_request(
            operation=Operation.DIAL,
            ua=ua,
            params=uri,
            sender=lambda token: self._call_protocol("dial", uri, token=token),
        )

    def mute(self, ua: UserAgent) -> None:
        self._run_on_current_call(
            ua=ua,
            final_operation=Operation.MUTE,
            final_params=None,
            final_sender=lambda token: self._call_protocol("mute", None, token=token),
        )

    def resume(self, ua: UserAgent) -> None:
        self._run_on_current_call(
            ua=ua,
            final_operation=Operation.RESUME,
            final_params=None,
            final_sender=lambda token: self._call_protocol("resume", None, token=token),
        )

    def accept(self, ua: UserAgent) -> None:
        state = self._ensure_known_ua(ua)
        if state.current_call_id is not None:
            return

        self._send_request(
            operation=Operation.ACCEPT,
            ua=ua,
            sender=lambda token: self._call_protocol("accept", None, token=token),
        )

    def hangup(self, ua: UserAgent) -> None:
        self._run_on_current_call(
            ua=ua,
            final_operation=Operation.HANGUP,
            final_params=None,
            final_sender=lambda token: self._call_protocol("hangup", None, token=token),
        )

    def hangup_all(self) -> None:
        self._send_request(
            operation=Operation.HANGUP_ALL,
            sender=lambda token: self._call_protocol("hangupall", None, token=token),
        )

    def callstat(self) -> None:
        self._send_request(
            operation=Operation.CALLSTAT,
            sender=lambda token: self._call_protocol("callstat", token=token),
        )

    def set_current_call(self, ua: UserAgent) -> None:
        state = self._ensure_known_ua(ua)
        if state.current_call_id is None:
            return

        self._send_request(
            operation=Operation.CALLFIND,
            ua=ua,
            params=state.current_call_id,
            sender=lambda token: self._call_protocol("callfind", state.current_call_id, token=token),
        )

    def shutdown(self) -> None:
        for ua, state in list(self._user_agents.items()):
            if state.created:
                try:
                    self.delete_user_agent(ua)
                except Exception as exc:
                    self.managerError.emit(f"failed to delete {ua} during shutdown: {exc}")

    def deleteLater(self) -> None:
        self.shutdown()
        super().deleteLater()

    # -------------------------------------------------------------------------
    # Request sending
    # -------------------------------------------------------------------------

    def _send_request(
        self,
        operation: Operation,
        sender: Callable[[str], None],
        ua: Optional[UserAgent] = None,
        params: Optional[str] = None,
        transaction_id: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> str:
        token = self._make_token(ua) if ua is not None else self._make_global_token(operation.value)

        rq = self.PendingRequest(
            token=token,
            operation=operation,
            ua=ua,
            params=params,
            meta={} if meta is None else dict(meta),
            transaction_id=transaction_id,
        )
        self._pending_requests[token] = rq

        try:
            sender(token)
        except Exception:
            self._pending_requests.pop(token, None)
            raise

        self.requestSent.emit(rq)
        return token

    def _call_protocol(self, method_name: str, *args: Any, token: str) -> Any:
        method = getattr(self._p, method_name)
        return method(*args, token)

    # -------------------------------------------------------------------------
    # Transaction engine
    # -------------------------------------------------------------------------

    def _next_transaction_id(self) -> str:
        self._transaction_seq += 1
        return f"tx:{self._transaction_seq}"

    def _start_transaction(
        self,
        final_operation: Operation,
        ua: Optional[UserAgent],
        steps: list[TransactionStep],
    ) -> str:
        if not steps:
            raise ValueError("transaction must contain at least one step")

        tx_id = self._next_transaction_id()
        tx = self.Transaction(
            id=tx_id,
            final_operation=final_operation,
            ua=ua,
            steps=steps,
        )
        self._transactions[tx_id] = tx
        self._transaction_queue.append(tx_id)
        self.transactionStarted.emit(tx)
        self._pump_transactions()
        return tx_id

    def _pump_transactions(self) -> None:
        if self._active_transaction_id is not None:
            return

        while self._transaction_queue:
            tx_id = self._transaction_queue[0]
            tx = self._transactions.get(tx_id)
            if tx is None:
                self._transaction_queue.popleft()
                continue

            self._active_transaction_id = tx_id
            self._send_current_transaction_step(tx)
            return

    def _send_current_transaction_step(self, tx: Transaction) -> None:
        step = tx.current_step()
        if step is None:
            self._finish_transaction_success(tx)
            return

        self._send_request(
            operation=step.operation,
            ua=step.ua,
            params=step.params,
            sender=step.sender,
            transaction_id=tx.id,
        )

    def _finish_transaction_success(self, tx: Transaction) -> None:
        self._transactions.pop(tx.id, None)

        if self._transaction_queue and self._transaction_queue[0] == tx.id:
            self._transaction_queue.popleft()
        else:
            try:
                self._transaction_queue.remove(tx.id)
            except ValueError:
                pass

        if self._active_transaction_id == tx.id:
            self._active_transaction_id = None

        self.transactionCompleted.emit(tx)
        self.transactionCompletedSimple.emit(tx.final_operation, tx.ua)
        self._pump_transactions()

    def _finish_transaction_failure(self, tx: Transaction, response: dict[str, Any]) -> None:
        self._transactions.pop(tx.id, None)

        if self._transaction_queue and self._transaction_queue[0] == tx.id:
            self._transaction_queue.popleft()
        else:
            try:
                self._transaction_queue.remove(tx.id)
            except ValueError:
                pass

        if self._active_transaction_id == tx.id:
            self._active_transaction_id = None

        self.transactionFailed.emit(tx, response)
        self._pump_transactions()

    def _handle_transaction_response(self, request: PendingRequest, response: dict[str, Any]) -> None:
        tx_id = request.transaction_id
        if tx_id is None:
            return

        tx = self._transactions.get(tx_id)
        if tx is None:
            return

        tx.responses.append(response)
        self.transactionStepFinished.emit(tx, response)

        if not bool(response.get("ok")):
            self._finish_transaction_failure(tx, response)
            return

        tx.index += 1
        if tx.finished:
            self._finish_transaction_success(tx)
            return

        self._send_current_transaction_step(tx)

    def _run_on_current_call(
        self,
        ua: UserAgent,
        final_operation: Operation,
        final_params: Optional[str],
        final_sender: Callable[[str], None],
    ) -> None:
        state = self._ensure_known_ua(ua)
        call_id = state.current_call_id
        if call_id is None:
            return

        steps = [
            self.TransactionStep(
                operation=Operation.CALLFIND,
                ua=ua,
                params=call_id,
                sender=lambda token, cid=call_id: self._call_protocol("callfind", cid, token=token),
            ),
            self.TransactionStep(
                operation=final_operation,
                ua=ua,
                params=final_params,
                sender=final_sender,
            ),
        ]
        self._start_transaction(final_operation=final_operation, ua=ua, steps=steps)

    # -------------------------------------------------------------------------
    # Response / event handling
    # -------------------------------------------------------------------------

    def _on_response(self, response: dict) -> None:
        token = str(response.get("token"))
        pending = self._pending_requests.pop(token, None)
        if pending is None:
            self.unknownResponse.emit(response)
            return

        self._apply_response(pending, response)
        self.requestFinished.emit(pending, response)
        self._handle_transaction_response(pending, response)

    def _apply_response(self, request: PendingRequest, response: dict) -> None:
        ok = bool(response.get("ok"))

        if request.operation == Operation.CREATE_UA:
            if ok and request.ua is not None:
                state = self._user_agents.get(request.ua)
                if state is not None:
                    state.created = True
                    self.userAgentCreated.emit(request.ua, response)

        elif request.operation == Operation.DELETE_UA:
            if ok and request.ua is not None:
                state = self._user_agents.get(request.ua)
                if state is not None:
                    state.created = False
                    state.reg_status = RegStatus.UNREGISTERED
                    state.current_call_id = None
                    state.current_call_line = None
                    state.last_event = "DELETED"
                    self.userAgentDeleted.emit(request.ua, response)

        elif request.operation == Operation.REQUEST_REGINFO:
            data = response.get("data")
            if ok and isinstance(data, str):
                self._update_reginfo_from_text(data)

        elif request.operation == Operation.CALLFIND:
            if ok and request.ua is not None:
                state = self._user_agents.get(request.ua)
                if state is not None:
                    data = response.get("data")
                    if isinstance(data, dict):
                        line = data.get("line")
                        if isinstance(line, int):
                            state.current_call_line = line

    def _on_event(self, event: dict) -> None:
        self._log.debug("event received: %s", event)
        self.eventReceived.emit(event)

        ev = Event(
            type=event.get("type"),
            aor=event.get("accountaor"),
            call_id=event.get("id"),
            peer_uri=event.get("peeruri"),
            param=event.get("param"),
            contact_uri=event.get("contacturi"),
            user=self._user_from_sip_uri(event.get("contacturi", ""))
        )

        state = self._ua_by_aor.get(ev.aor)
        if state is None:
            return

        if ev.type in {
            "REGISTERING",
            "REGISTER_OK",
            "REGISTER_FAIL",
            "UNREGISTERING",
            "UNREGISTER_OK",
        }:
            self._apply_registration_event(state, ev.type)
            return

        if ev.type == "CALL_INCOMING":
            self.incomingCall.emit(state.ua, ev)
            return

        if ev.type == "CALL_ESTABLISHED":
            state.current_call_id = ev.call_id
            self.callEstablished.emit(state.ua, ev)
            return

        if ev.type == "CALL_CLOSED":
            state.current_call_id = None
            state.current_call_line = None
            self.callClosed.emit(state.ua, ev)
            return

    def _on_message(self, message: dict) -> None:
        self._log.debug("message received: %s", message)
        self.messageReceived.emit(message)

    def _on_error(self, msg: str) -> None:
        self._log.error("error: %s", msg)

    def _on_request_sent(self, rq: PendingRequest) -> None:
        if self._log.isEnabledFor(logging.DEBUG):
            data = dataclasses.asdict(rq)
            data["operation"] = rq.operation.value
            self._log.debug("request sent: %s", data)

    # -------------------------------------------------------------------------
    # Registration state helpers
    # -------------------------------------------------------------------------

    def _apply_registration_event(self, state: UserAgentState, event_type: str) -> None:
        status = state.reg_status

        if event_type == "REGISTER_OK":
            status = RegStatus.REGISTERED
            state.created = True
        elif event_type == "REGISTERING":
            status = RegStatus.PENDING
            state.created = True
        elif event_type in {"REGISTER_FAIL", "UNREGISTERING", "UNREGISTER_OK"}:
            status = RegStatus.UNREGISTERED

        changed = (
            state.reg_status != status
            or state.last_event != event_type
        )

        state.reg_status = status
        state.last_event = event_type

        if changed:
            self.userAgentRegistrationChanged.emit(state.ua, state.reg_status)

    def _update_reginfo_from_text(self, text: str) -> None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            aor = self._extract_first_aor(line)
            if aor is None:
                continue

            state = self._ua_by_aor.get(aor)
            if state is None:
                continue

            status = RegStatus.PENDING
            low = line.lower()
            if "registered" in low:
                status = RegStatus.REGISTERED
                event_type = "REGINFO_REGISTERED"
                state.created = True
            elif "registering" in low:
                status = RegStatus.PENDING
                event_type = "REGINFO_REGISTERING"
                state.created = True
            elif "failed" in low or "unregistered" in low:
                status = RegStatus.UNREGISTERED
                event_type = "REGINFO_UNREGISTERED"
            else:
                continue

            changed = (
                state.reg_status != status
                or state.last_event != event_type
            )

            state.reg_status = status
            state.last_event = event_type

            if changed:
                self.userAgentRegistrationChanged.emit(state.ua, status)

    # -------------------------------------------------------------------------
    # Token / state helpers
    # -------------------------------------------------------------------------

    def _make_token(self, ua: UserAgent) -> str:
        aor = self._aor_of(ua)
        seq = self._sequence_by_key.get(aor, 0) + 1
        self._sequence_by_key[aor] = seq
        return f"{aor}:{seq}"

    def _make_global_token(self, prefix: str) -> str:
        seq = self._sequence_by_key.get(prefix, 0) + 1
        self._sequence_by_key[prefix] = seq
        return f"{prefix}:{seq}"

    def _ensure_known_ua(self, ua: UserAgent) -> UserAgentState:
        state = self._user_agents.get(ua)
        if state is not None:
            return state
        raise ValueError(f"user agent not added: {self._aor_of(ua)}")

    @staticmethod
    def _aor_of(ua: UserAgent) -> str:
        return f"sip:{ua.user}@{ua.domain}"

    @staticmethod
    def _account_line_of(ua: UserAgent) -> str:
        return f'<sip:{ua.user}@{ua.domain}>;auth_pass="{ua.password}"'

    @staticmethod
    def _extract_first_aor(text: str) -> Optional[str]:
        start = text.find("sip:")
        if start < 0:
            return None

        end = len(text)
        for sep in (" ", "\t", ">", "]", ";", ","):
            pos = text.find(sep, start)
            if pos >= 0:
                end = min(end, pos)

        return text[start:end]

    @staticmethod
    def _user_from_sip_uri(uri: str) -> Optional[str]:
        start_index = uri.find(":")
        if start_index == -1:
            return None

        end_index = uri.find("@")
        if end_index == -1:
            return None

        return uri[start_index + 1:end_index]
