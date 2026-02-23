# Telegram Anti-Spam Bot + VPN

Проект Telegram-бота для модерации чатов (удаление спама) и выдачи VPN-доступа пользователям через Outline.

Документация:
- `docs/protocol.md` — протокол модерации и выдачи VPN-доступа

## Запуск
1. Установить зависимости:
   - `pip install -r requirements.txt`
2. Задать переменные окружения:
   - `BOT_TOKEN` (обязателен)
   - `ADMIN_CHAT_ID` (опционально, куда слать уведомления)
   - `ADMIN_USER_IDS` (опционально, user_id админов через запятую)
   - `SPAM_KEYWORDS` (опционально, список через запятую)
   - `SPAM_DOMAINS` (опционально, blacklist доменов через запятую)
   - `ALLOW_DOMAINS` (опционально, whitelist доменов через запятую)
   - `MAX_LINKS` (опционально, по умолчанию `2`)
   - `REPEAT_WINDOW_SEC` (опционально, по умолчанию `300`)
   - `REPEAT_THRESHOLD` (опционально, по умолчанию `2`)
3. Запуск:
   - `python -m src.main`

## Команды бота
- `/spam_add keyword <слово>` — добавить ключевое слово в blacklist
- `/spam_add domain <домен>` — добавить домен в blacklist
- `/spam_remove keyword <слово>` — удалить ключевое слово
- `/spam_remove domain <домен>` — удалить домен
- `/spam_stats` — показать текущую политику
- `/vpn` — получить Outline ключ (пока заглушка)
