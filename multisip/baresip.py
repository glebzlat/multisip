import time
import logging
import threading
import pexpect

from typing import Optional, Callable
from datetime import timedelta

from .user_agent import Status as UserAgentStatus


def handle_expect(expectation: str | tuple[str]):

    def expect_decorator(meth):
        nonlocal expectation
        if isinstance(expectation, str):
            expectation = (expectation,)
        setattr(meth, "_expectation", expectation)
        return meth

    return expect_decorator


class BareSIP:

    def __init__(self, user_agent, log_level=logging.ERROR):
        self._timeout = timedelta(seconds=5)
        self._timeout_check_frequency_hz = 1000
        self._logger = None

        self._process = None
        self._thread = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._is_ready = False

        self._user_agent = user_agent
        self._user_agent_status = None

        self._semaphore_user_agents = 0

        self._handlers: dict[tuple[str], Callable] = {}
        for mem_name in dir(self):
            mem = getattr(self, mem_name)
            if (exp := getattr(mem, "_expectation", None)) is not None:
                self._handlers[exp] = mem

        self._line_chars = []
        self._line = None

        self._expectations = list(self._handlers.keys())

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(log_level)

        self._pid = 0

    def is_running(self):
        return self._is_running

    def is_ready(self):
        return self._is_ready

    def start(self) -> UserAgentStatus:
        self._process = pexpect.spawn('baresip', encoding='utf-8')
        self._pid = self._process.pid

        self._thread = threading.Thread(target=self._parse, daemon=True)
        self._thread.start()

        self._is_running = True
        self._wait_for_ready()

        return self._create_user_agent()

    def stop(self):
        if not self._stop_event.is_set():
            self._stop_event.set()

        if self._thread is not None:
            self._thread.join()
            self._log_debug("parser thread stopped")
            self._thread = None
            self._process = None

        if self._process:
            self._send("/quit")
            self._process.wait()
            self._process.terminate()
            self._log_debug("baresip stopped")

        self._is_running = False

    def get_user_agent_status(self) -> Optional[UserAgentStatus]:
        # Wait for response using semaphore
        # Increase semaphore value before sending command, since it will
        # immediately produce output
        self._semaphore_user_agents = 1

        self._send("/reginfo")

        # Wait for resources to be released before continuing
        for _ in range(self._timeout_check_frequency_hz * self._timeout.seconds):
            if not self._semaphore_user_agents == 1:
                return self._user_agent_status

            time.sleep(1 / self._timeout_check_frequency_hz)

        self._log_error("timeout waiting for user agents")

        return None

    def dial(self, address: str):
        self._log_debug("Dial %s", address)
        self._send(f"/dial {address}")

    def hangup(self):
        self._log_debug("Hangup")
        self._send("/hangup")

    def hangup_all(self):
        self._log_debug("Hangup all")
        self._send("/hangupall")

    def answer(self):
        self._log_debug("Answer")
        self._send("/accept")

    def __del__(self):
        if self._process:
            self.stop()

    def _create_user_agent(self) -> Optional[UserAgentStatus]:
        # Wait for response using semaphore
        # Increase semaphore value before sending command, since it will
        # immediately produce output
        self._semaphore_user_agents = 2

        ua = self._user_agent
        self._send(f"/uanew <sip:{ua.user}@{ua.domain}>;auth_pass=\"{ua.password}\"")

        for _ in range(self._timeout_check_frequency_hz * self._timeout.seconds):
            if not self._semaphore_user_agents == 2:
                return self._user_agent_status

            time.sleep(1 / self._timeout_check_frequency_hz)

        self._log_error("timeout waiting for user agents")

        return None

    def _send(self, command: str) -> bool:
        if self._is_ready:
            self._process.sendline(command)
            return True
        else:
            self._log_error("attempt to write while process is not running")
            return False

    def _parse(self):
        self._log_debug("output parser active")

        while not self._stop_event.is_set():
            self._read_char()
            if self._line:
                self._process_line()
                self._clear_line()

        self._log_debug("output parser stopped")

    def _read_char(self):
        try:
            c = self._process.read_nonblocking(1, timeout=0)
            self._line_chars.append(c)
            if c == "\n":
                self._line = "".join(self._line_chars)
        except pexpect.TIMEOUT:
            pass

    def _clear_line(self):
        self._line = None
        self._line_chars.clear()

    def _process_line(self):
        try:
            for expectations, handler in self._handlers.items():
                for expect in expectations:
                    if expect in self._line:
                        handler()
        except pexpect.EOF:
            self._log_error("parser recieved EOF")
            self.stop()
        except pexpect.TIMEOUT:
            pass
        except Exception as e:
            self._log_error("error reading line", e)

    @handle_expect("baresip is ready.")
    def _handle_ready(self):
        self._is_ready = True
        self._logger.debug("baresip is ready")
        self.handle_ready()

    @handle_expect("--- User Agents ")
    def _handle_uas_list(self):
        line = self._line

        agents_count = int(line[line.index("(") + 1:line.index(")")])
        assert agents_count == 1

        self._process.expect(["0", ">"])
        line = self._process.readline()
        for status in UserAgentStatus:
            if status.value in line:
                self._user_agent_status = status
                break

        # Release semaphore
        self._semaphore_user_agents = 0

    @handle_expect("useragent registered successfully")
    def _handle_register(self):
        self.handle_register()

    @handle_expect("Call in-progress: ")
    def _handle_in_progress(self):
        uri = self._line.split(":")[1].strip()
        self._log_debug(f"call in-progress: {uri}")
        self.handle_call_in_progress(uri)

    @handle_expect("Call answered: ")
    def _handle_answered(self):
        uri = self._line.split(":")[1].strip()
        self._log_debug(f"call answered: {uri}")
        self.handle_call_answered(uri)

    @handle_expect("session closed")
    def _handle_hangup(self):
        line = self._line
        reason = line.split("session closed:")[1].strip()
        uri = line.split(": session closed:")[0].strip()
        self._log_debug(f"call with {uri} terminated: {reason}")
        self.handle_hangup_call(uri, reason)

    @handle_expect("could not find UA")
    def _handle_no_ua(self):
        self._log_error("attempted to dial without registered user agent")

    @handle_expect("Incoming call from: ")
    def _handle_incoming_call(self):
        line = self._line
        uri = line.split("Incoming call from: ")[1].split(" - ")[0].strip()
        self._log_debug(f"Incoming call from: {uri}")
        self.handle_incoming_call(uri)

    def _wait_for_ready(self):
        for _ in range(self._timeout.seconds * self._timeout_check_frequency_hz):
            if self._is_ready:
                return
            time.sleep(1 / self._timeout_check_frequency_hz)

    def _log_error(self, message: str, *args):
        if self._logger.level <= logging.ERROR:
            self._logger.error(f"{self._user_agent.user}:{self._pid}: {message}", *args)

    def _log_info(self, message: str, *args):
        if self._logger.level <= logging.INFO:
            self._logger.info(f"{self._user_agent.user}:{self._pid}: {message}", *args)

    def _log_debug(self, message: str, *args):
        if self._logger.level <= logging.DEBUG:
            self._logger.debug(f"{self._user_agent.user}:{self._pid}: {message}", *args)

    def handle_ready(self):
        pass

    def handle_register(self):
        pass

    def handle_call_in_progress(self, uri: str):
        pass

    def handle_call_answered(self, uri: str):
        pass

    def handle_incoming_call(self, uri: str):
        pass

    def handle_hangup_call(self, uri: str, reason: str):
        pass
