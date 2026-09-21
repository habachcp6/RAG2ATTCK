"""Inherited network audit hook for the offline test launcher (not a sandbox)."""

import os
import sys


def _append(path: str, message: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, message.encode("ascii"))
    finally:
        os.close(descriptor)


_journal = os.environ.get("RAG2ATTCK_OFFLINE_JOURNAL")
if _journal:
    _append(_journal, f"START {os.getpid()}\n")

    def _deny_network(event: str, args: tuple) -> None:
        if event in {
            "socket.connect",
            "socket.getaddrinfo",
            "socket.sendto",
            "socket.sendmsg",
        }:
            _append(_journal, f"DENIED {os.getpid()} {event}\n")
            raise RuntimeError("Offline test guard blocked network access")

    sys.addaudithook(_deny_network)
