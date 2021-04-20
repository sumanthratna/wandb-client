# File is generated by: tox -e codemod
# -*- coding: utf-8 -*-
"""Internal utility routines.

Collection of classes to support the internal process.

"""

from __future__ import print_function

import logging
import sys
import threading

from six.moves import queue
import wandb


if wandb.TYPE_CHECKING:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Tuple, Type, Optional, Union
        from six.moves.queue import Queue
        from wandb.proto.wandb_internal_pb2 import Record, Result
        from threading import Event
        from types import TracebackType

        ExceptionType = Union[
            Tuple[Type[BaseException], BaseException, TracebackType],
            Tuple[None, None, None],
        ]


logger = logging.getLogger(__name__)


class ExceptionThread(threading.Thread):
    """Class to catch exceptions when running a thread."""

    # __stopped: "Event"
    # __exception: "Optional[ExceptionType]"

    def __init__(self, stopped):
        threading.Thread.__init__(self)
        self.__stopped = stopped
        self.__exception = None

    def _run(self):
        raise NotImplementedError

    def run(self):
        try:
            self._run()
        except Exception:
            self.__exception = sys.exc_info()
        finally:
            if self.__exception and self.__stopped:
                self.__stopped.set()

    def get_exception(self):
        return self.__exception


class RecordLoopThread(ExceptionThread):
    """Class to manage reading from queues safely."""

    def __init__(
        self,
        input_record_q,
        result_q,
        stopped,
    ):
        ExceptionThread.__init__(self, stopped=stopped)
        self._input_record_q = input_record_q
        self._result_q = result_q
        self._stopped = stopped

    def _setup(self):
        raise NotImplementedError

    def _process(self, record):
        raise NotImplementedError

    def _finish(self):
        raise NotImplementedError

    def _run(self):
        self._setup()
        while not self._stopped.is_set():
            try:
                record = self._input_record_q.get(timeout=1)
            except queue.Empty:
                continue
            self._process(record)
        self._finish()