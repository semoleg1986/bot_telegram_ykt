from src.domain import Policy
from src.interface.telegram.utils import (
    apply_policy_add,
    apply_policy_remove,
    format_policy_summary,
    split_args,
)


def test_split_args():
    assert split_args("/spam_add keyword word") == ["/spam_add", "keyword", "word"]
    assert split_args("") == []


def test_format_policy_summary():
    policy = Policy(keyword_list=("one",), domain_blacklist=("bad",))
    summary = format_policy_summary(policy)
    assert "ключевые слова: 1" in summary
    assert "blacklist доменов: 1" in summary


def test_apply_policy_add_keyword():
    policy = Policy(keyword_list=("one",))
    updated = apply_policy_add(policy, "keyword", "two")
    assert updated.keyword_list == ("one", "two")


def test_apply_policy_add_domain():
    policy = Policy(domain_blacklist=("bad.example",))
    updated = apply_policy_add(policy, "domain", "evil.example")
    assert "evil.example" in updated.domain_blacklist


def test_apply_policy_remove_keyword():
    policy = Policy(keyword_list=("one", "two"))
    updated = apply_policy_remove(policy, "keyword", "one")
    assert updated.keyword_list == ("two",)


def test_apply_policy_remove_domain():
    policy = Policy(domain_blacklist=("bad.example", "evil.example"))
    updated = apply_policy_remove(policy, "domain", "bad.example")
    assert updated.domain_blacklist == ("evil.example",)
