from ednna.chat.facade import try_orchestrated_chat


def test_orchestrated_chat_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ORCHESTRATED_CHAT_ENABLED", raising=False)

    assert try_orchestrated_chat("qual o status EDI?") is None
