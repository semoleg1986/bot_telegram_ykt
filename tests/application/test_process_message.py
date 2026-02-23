import asyncio

from src.application import ProcessMessage
from src.domain import Message, Policy, User
from src.infrastructure import (
    InMemoryContextProvider,
    InMemoryDecisionLogger,
    InMemoryMessageAction,
    InMemoryPolicyStore,
)


def test_process_message_deletes_and_logs():
    policy = Policy(keyword_list=("spam",))
    context = InMemoryContextProvider()
    logger = InMemoryDecisionLogger()
    actions = InMemoryMessageAction()
    policy_store = InMemoryPolicyStore(policy=policy)
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context,
        logger=logger,
        actions=actions,
    )

    message = Message.from_text(1, 100, 10, "spam offer")
    result = asyncio.run(use_case.execute(message, User(user_id=10)))

    assert result.decision == "deleted"
    assert actions.deleted == [(100, 1)]
    assert len(logger.entries) == 1


def test_process_message_allows_and_logs():
    policy = Policy(keyword_list=("spam",))
    context = InMemoryContextProvider()
    logger = InMemoryDecisionLogger()
    actions = InMemoryMessageAction()
    policy_store = InMemoryPolicyStore(policy=policy)
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context,
        logger=logger,
        actions=actions,
    )

    message = Message.from_text(1, 100, 10, "hello")
    result = asyncio.run(use_case.execute(message, User(user_id=10)))

    assert result.decision == "allowed"
    assert actions.deleted == []
    assert len(logger.entries) == 1


def test_process_message_notifies_when_enabled():
    policy = Policy(keyword_list=("spam",))
    context = InMemoryContextProvider()
    logger = InMemoryDecisionLogger()
    actions = InMemoryMessageAction()
    policy_store = InMemoryPolicyStore(policy=policy)
    use_case = ProcessMessage(
        policy_store=policy_store,
        context_provider=context,
        logger=logger,
        actions=actions,
        notify_on_delete=True,
    )

    message = Message.from_text(1, 100, 10, "spam offer")
    asyncio.run(use_case.execute(message, User(user_id=10)))

    assert actions.notifications
