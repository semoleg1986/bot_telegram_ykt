import asyncio

from src.application import LogEntry
from src.domain import Policy, SpamDecision
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryMessageAction,
    InMemoryPolicyStore,
    StubVpnIssuer,
)


def test_in_memory_context_provider_stores_texts():
    provider = InMemoryContextProvider()
    provider.add_text(1, 10, "hello")
    provider.add_text(1, 10, "world")
    assert asyncio.run(provider.get_recent_texts(1, 10, 300)) == ("hello", "world")


def test_in_memory_logger_collects_entries():
    logger = InMemoryDecisionLogger()
    entry = LogEntry(
        chat_id=1,
        message_id=2,
        user_id=3,
        decision=SpamDecision(is_spam=False),
        policy=Policy(),
    )
    asyncio.run(logger.log(entry))
    assert logger.entries == [entry]


def test_in_memory_actions_track_operations():
    actions = InMemoryMessageAction()
    asyncio.run(actions.delete_message(1, 2))
    asyncio.run(actions.notify_admins(1, "deleted"))
    assert actions.deleted == [(1, 2)]
    assert actions.notifications == [(1, "deleted")]


def test_in_memory_policy_store_updates_policy():
    store = InMemoryPolicyStore(policy=Policy(keyword_list=("one",)))
    updated = asyncio.run(
        store.update(lambda p: Policy(keyword_list=p.keyword_list + ("two",)))
    )
    assert updated.keyword_list == ("one", "two")


def test_stub_vpn_issuer_returns_key():
    issuer = StubVpnIssuer()
    key = asyncio.run(issuer.issue(42))
    assert "42" in key
