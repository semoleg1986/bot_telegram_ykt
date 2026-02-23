from __future__ import annotations

from dataclasses import dataclass

from src.domain import Message, SpamContext, User, evaluate_message

from .interfaces import (
    ContextProvider,
    DecisionLogger,
    LogEntry,
    MessageAction,
    PolicyStore,
)


@dataclass(frozen=True)
class ProcessMessageResult:
    decision: str
    reason: str


@dataclass
class ProcessMessage:
    policy_store: PolicyStore
    context_provider: ContextProvider
    logger: DecisionLogger
    actions: MessageAction
    notify_on_delete: bool = False

    async def execute(self, message: Message, user: User) -> ProcessMessageResult:
        policy = await self.policy_store.get()
        recent_texts = await self.context_provider.get_recent_texts(
            chat_id=message.chat_id,
            user_id=message.user_id,
            window_sec=policy.repeat_window_sec,
        )
        context = SpamContext.from_texts(recent_texts)
        decision = evaluate_message(message, user, policy, context)

        await self.logger.log(
            LogEntry(
                chat_id=message.chat_id,
                message_id=message.message_id,
                user_id=message.user_id,
                decision=decision,
                policy=policy,
            )
        )

        if decision.is_spam:
            await self.actions.delete_message(message.chat_id, message.message_id)
            if self.notify_on_delete and decision.primary_reason:
                await self.actions.notify_admins(
                    message.chat_id,
                    (
                        f"Удалено сообщение {message.message_id}: "
                        f"{decision.primary_reason}"
                    ),
                )
            return ProcessMessageResult(
                decision="deleted", reason=decision.primary_reason
            )

        return ProcessMessageResult(decision="allowed", reason=decision.primary_reason)
