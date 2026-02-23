from src.domain import Message, Policy, SpamContext, User, evaluate_message


def test_whitelist_domain_overrides_keyword():
    policy = Policy(
        keyword_list=("spam",),
        domain_whitelist=("safe.example",),
    )
    message = Message.from_text(1, 1, 1, "spam here").with_urls(
        ("https://safe.example/info",)
    )
    decision = evaluate_message(message, User(user_id=1), policy, SpamContext())
    assert decision.is_spam is False


def test_multiple_matches_collected():
    policy = Policy(keyword_list=("spam",), domain_blacklist=("bad.example",))
    message = Message.from_text(1, 1, 1, "spam here").with_urls(
        ("https://bad.example",)
    )
    decision = evaluate_message(message, User(user_id=1), policy, SpamContext())
    assert decision.is_spam is True
    assert len(decision.matches) >= 2
