from src.domain import Message, Policy, SpamContext, User, evaluate_message


def test_keyword_match_marks_spam():
    policy = Policy(keyword_list=("buy now",))
    message = Message.from_text(1, 100, 10, "Please BUY now, best deal")
    decision = evaluate_message(message, User(user_id=10), policy, SpamContext())
    assert decision.is_spam is True
    assert decision.primary_reason.startswith("Ключевое слово")


def test_blocklisted_domain_marks_spam():
    policy = Policy(domain_blacklist=("bad.example",))
    message = Message.from_text(1, 100, 10, "check this").with_urls(
        ("https://bad.example/offer",)
    )
    decision = evaluate_message(message, User(user_id=10), policy, SpamContext())
    assert decision.is_spam is True
    assert decision.primary_reason.startswith("Запрещенный домен")


def test_whitelisted_domain_allows_message():
    policy = Policy(
        keyword_list=("buy",),
        domain_blacklist=("bad.example",),
        domain_whitelist=("safe.example",),
    )
    message = Message.from_text(1, 100, 10, "buy now").with_urls(
        ("https://safe.example/info",)
    )
    decision = evaluate_message(message, User(user_id=10), policy, SpamContext())
    assert decision.is_spam is False


def test_link_overflow_marks_spam():
    policy = Policy(max_links=1)
    message = Message.from_text(1, 100, 10, "links").with_urls(
        ("https://a.example", "https://b.example")
    )
    decision = evaluate_message(message, User(user_id=10), policy, SpamContext())
    assert decision.is_spam is True
    assert decision.primary_reason.startswith("Слишком много ссылок")


def test_repeat_rule_marks_spam():
    policy = Policy(repeat_threshold=2)
    context = SpamContext.from_texts(("hello", "hello"))
    message = Message.from_text(1, 100, 10, "hello")
    decision = evaluate_message(message, User(user_id=10), policy, context)
    assert decision.is_spam is True
    assert decision.primary_reason.startswith("Повтор сообщения")


def test_admin_is_exempt():
    policy = Policy(keyword_list=("buy",))
    message = Message.from_text(1, 100, 10, "buy now")
    decision = evaluate_message(
        message, User(user_id=10, is_admin=True), policy, SpamContext()
    )
    assert decision.is_spam is False
