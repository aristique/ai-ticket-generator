import asyncio

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output import DummyOutput

from tickets.cli import BINDINGS, read_required, run
from tickets.journal import JournalBusy


class ScriptedSession:
    def __init__(self, values):
        self.values = iter(values)

    def prompt(self, label):
        value = next(self.values)
        if isinstance(value, BaseException):
            raise value
        return value


class RecordingJournal:
    def __init__(self, fail_once=False):
        self.entries = []
        self.fail_once = fail_once

    def append(self, entry):
        if self.fail_once:
            self.fail_once = False
            raise JournalBusy("Закройте Excel")
        self.entries.append(entry)


def test_blank_field_reprompts_and_trims():
    session = ScriptedSession(["", "  ", "  Иванов "])
    assert read_required(session, "Last name: ") == "Иванов"


def test_save_retry_keeps_same_ticket_and_does_not_duplicate():
    journal = RecordingJournal(fail_once=True)
    messages = []
    calls = []
    def generate():
        calls.append(1)
        return 7
    run(ScriptedSession(["Иванов", "Иван", "", EOFError()]),
        journal, generate, messages.append)
    assert len(calls) == 1
    assert len(journal.entries) == 1
    assert journal.entries[0].ticket == 7
    assert any("Билет № 7" in message for message in messages)


@pytest.mark.parametrize("values", [[EOFError()], ["Иванов", EOFError()]])
def test_exit_during_either_name_does_not_save_partial_entry(values):
    journal = RecordingJournal()
    assert run(ScriptedSession(values), journal, output=lambda _: None) == 0
    assert not journal.entries


def test_real_escape_key_finishes_prompt_without_enter():
    async def scenario():
        with create_pipe_input() as stream:
            session = PromptSession(input=stream, output=DummyOutput(),
                                    key_bindings=BINDINGS)
            session.app.ttimeoutlen = 0.05
            task = asyncio.create_task(session.prompt_async("Last name: "))
            await asyncio.sleep(0.05)
            stream.send_text("\x1b")
            with pytest.raises(EOFError):
                await asyncio.wait_for(task, timeout=2)
    asyncio.run(scenario())

