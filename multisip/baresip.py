import time
import logging
import threading
import pexpect
import enum
import types

from typing import Optional, Callable
from datetime import timedelta

from .user_agent import Status as UserAgentStatus


def handle_expectation(expectation: str):

    def expect_decorator(meth):
        setattr(meth, "_expectation", expectation)
        return meth

    return expect_decorator


class BareSIP:

    _handlers: dict[str, Callable] = {}

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        for mem_name in dir(cls):
            mem = getattr(obj, mem_name)
            if (expectation := getattr(mem, "_expectation", None)) is not None:
                assert callable(mem)
                obj._handlers[expectation] = mem
        return obj

    # Types
    class Event(enum.Enum):
        READY = "READY",
        CALLING = "CALLING",
        ANSWERED = "ANSWERED",
        INCOMING_CALL = "INCOMING_CALL",
        TERMINATED = "TERMINATED",
        UA_REGISTED = "UA_REGISTED",

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

        self._callbacks = {
            self.Event.READY: None,
            self.Event.INCOMING_CALL: None,
            self.Event.CALLING: None,
            self.Event.ANSWERED: None,
            self.Event.TERMINATED: None,
            self.Event.UA_REGISTED: None,
        }

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.propagate = 0
        self._logger.setLevel(log_level)

        self._pid = 0

    def is_running(self):
        return self._is_running

    def is_ready(self):
        return self._is_ready

    def __del__(self):
        if self._process:
            self.stop()

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
            self._process_line()

        self._log_debug("output parser stopped")

    def _process_line(self):
        try:
            # TODO - compile list pattern
            expectations = [
                "baresip is ready.",
                "--- User Agents ",
                "useragent registered successfully",
                "Incoming call from: ",
                "Call in-progress: ",
                "could not find UA",
                "Call answered: ",
                "session closed",
            ]

            # print(self._process.readline().strip())

            expectation = expectations[self._process.expect(expectations, timeout=0)]

            if expectation == "baresip is ready.":
                self._is_ready = True

                self._log_debug("baresip is ready")

                if isinstance(self._callbacks[self.Event.READY], types.FunctionType):
                    self._callbacks[self.Event.READY]()

                return

            if expectation == "--- User Agents ":
                # Process output format: "--- User Agents (#)"
                # ......................."0: <sip:user@domain> - OK"
                # ......................."1: <sip:user@domain> - zzz"
                line = self._process.readline().strip()

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

                return

            if expectation == "useragent registered successfully":
                if isinstance(self._callbacks[self.Event.UA_REGISTED], types.FunctionType):
                    self._callbacks[self.Event.UA_REGISTED]()

                return

            # User dialed a number, went through
            if expectation == "Call in-progress: ":
                uri = self._process.readline().strip()

                self._log_debug(f"call in-progress: {uri}")

                if isinstance(self._callbacks[self.Event.CALLING], types.FunctionType):
                    self._callbacks[self.Event.CALLING](uri)

                return

            # Other client answered
            if expectation == "Call answered: ":
                uri = self._process.readline().strip()

                self._log_debug(f"call answered: {uri}")

                if isinstance(self._callbacks[self.Event.ANSWERED], types.FunctionType):
                    self._callbacks[self.Event.ANSWERED](uri)

                return

            # Other client hung up
            if expectation == "session closed":
                self._process.readline()
                line = self._process.readline().strip()

                uri = ''.join(line.split("Call with ")[1].split(" terminated")[0])

                self._log_debug(f"call terminated: {uri}")

                if isinstance(self._callbacks[self.Event.TERMINATED], types.FunctionType):
                    self._callbacks[self.Event.TERMINATED](uri)

            # No user agent
            if expectation == "could not find UA":
                self._log_error("attempted to dial without registered user agent")
                return

            # Incoming call
            if expectation == "Incoming call from: ":
                line = self._process.readline().strip()
                uri = line[line.index(" ") + 1:line.index(" - ")]

                self._log_debug(f"incoming call from: {uri}")

                if isinstance(self._callbacks[self.Event.INCOMING_CALL], types.FunctionType):
                    self._callbacks[self.Event.INCOMING_CALL](uri)

                return

        except pexpect.EOF:
            self._log_error("parser recieved EOF")
            self.stop()
        except pexpect.TIMEOUT:
            pass
        except Exception as e:
            self._log_error("error reading line", e)
        return

    def _wait_for_ready(self):
        for _ in range(self._timeout.seconds * self._timeout_check_frequency_hz):
            if self._is_ready:
                return
            time.sleep(1 / self._timeout_check_frequency_hz)

    # Public methods
    def start(self): #TODO - Arguments for config
        # Create process
        self._process = pexpect.spawn('baresip', encoding='utf-8')
        # Do parsing on separate thread
        self._thread = threading.Thread(target=self._parse, daemon=True)
        self._thread.start()

        self._is_running = True
        self._wait_for_ready()

    def stop(self):
        # Stop Parser
        if not self._stop_event.is_set():
            self._stop_event.set()

        # Delete parser thread
        if self._thread is not None:
            self._thread.join()
            self._log_debug("parser thread stopped")
            self._thread = None
            self._process = None

        # Stop process
        if self._process:
            self._send("/quit")
            self._process.wait()
            self._process.terminate()
            self._log_debug("baresip stopped")

        self._is_running = False

    # Sets callbacks for events
    def on(self, event: Event, callback: types.FunctionType) -> bool:
        self._callbacks[event] = callback

    # /reginfo
    def get_user_agent_status(self):
        # Wait for response using semaphore
        # Increase semaphore value before sending command, since it will
        # immediately produce output
        self._semaphore_user_agents = 1

        # Send command
        self._send("/reginfo")

        # Wait for resources to be released before continuing
        for _ in range(self._timeout_check_frequency_hz * self._timeout.seconds):
            if not self._semaphore_user_agents == 1:
                return self._user_agent_status

            time.sleep(1 / self._timeout_check_frequency_hz)

        self._log_error("timeout waiting for user agents")

        return None

    # /uanew
    def create_user_agent(self) -> Optional[UserAgentStatus]:
        # Wait for response using semaphore
        # Increase semaphore value before sending command, since it will
        # immediately produce output
        self._semaphore_user_agents = 2

        ua = self._user_agent
        self._send(f"/uanew <sip:{ua.user}@{ua.domain}>;auth_pass=\"{ua.password}\"")

        # Wait for resources to be released before continuing
        for _ in range(self._timeout_check_frequency_hz * self._timeout.seconds):
            if not self._semaphore_user_agents == 2:
                return self._user_agent_status

            time.sleep(1 / self._timeout_check_frequency_hz)

        self._log_error("timeout waiting for user agents")

        return None

    # /dial
    def dial(self, address: str):
        self._send(f"/dial {address}")

    # /hangup
    def hangup(self):
        self._send("/hangup")

    # /hangupall
    def hangup_all(self):
        self._send("/hangupall")

    # /answer
    def answer(self):
        self._send("/answer")

    def _log_error(self, message: str, *args):
        if self._logger.level >= logging.ERROR:
            self._logger.error(f"BareSIP<{self._pid}>: {message}", *args)

    def _log_info(self, message: str, *args):
        if self._logger.level >= logging.INFO:
            self._logger.info(f"BareSIP<{self._pid}>: {message}", *args)

    def _log_debug(self, message: str, *args):
        if self._logger.level >= logging.DEBUG:
            self._logger.debug(f"BareSIP<{self._pid}>: {message}", *args)
