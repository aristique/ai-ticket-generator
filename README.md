# Генератор экзаменационных билетов

Лабораторные №1 и №2. Каждая работа запускается отдельно в Docker на Linux и Windows 11 с Docker Desktop в режиме Linux containers.

| Работа | Запуск | Результаты |
| --- | --- | --- |
| №1 — консоль | `docker compose run --rm lab1` | `data/lab1/journal.xlsx` |
| №2 — настольный интерфейс | `docker compose up -d lab2` | `data/lab2/results.xlsx` |

Первый запуск: `docker compose build lab1`. Проверки: `docker compose run --rm test-lab1`.

Запускайте команды из корня репозитория в терминале Linux или PowerShell. Для №1 нужен интерактивный терминал. Системный Python устанавливать не нужно. Файлы журнала остаются в папке `data` после удаления контейнеров.

Для №2 сначала выполните `docker compose build lab2 test-lab2`, затем `docker compose run --rm lab2 python -m ui_tickets.samples /data` для явного создания вымышленных входных данных. Откройте http://localhost:6082/vnc.html?autoconnect=true&resize=scale. Тесты: `docker compose run --rm test-lab2`. Подробности — [инструкция №2](lab2-desktop/README.md).

Лабораторные №3 и №4 требуют собственных репозиториев; они не будут добавляться сюда. По явному решению пользователя все приложения реализуются Codex; предписанные Copilot и Antigravity не используются.

Подробности: [план](docs/PLAN.md), [проверка Windows](docs/WINDOWS.md), [использование ИИ](docs/AI_WORKFLOW.md).
