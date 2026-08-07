<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | **[Русский](README.md)** | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> Превращает **GeekMagic SmallTV** в дисплей статуса агента в реальном времени — для Claude Code, Codex и agy.

Маленький экран показывает, чем занят ваш агент прямо сейчас: **WORKING**, **APPROVAL NEEDED** или **DONE** — а также модель, процент заполнения контекстного окна и количество токенов, взятые в реальном времени из транскрипта сессии.
Главная фишка — красный экран **APPROVAL**: разместите агента на другом мониторе, и вы сможете отойти, бросить взгляд и в тот же момент узнать, что он ждёт вашего подтверждения, вместо того чтобы обнаружить это десять минут спустя.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (янтарный) + сам промпт |
| approval needed | ⛔ **APPROVAL** (красный) + что требуется |
| turn finished | ✓ **DONE** (зелёный) |

Каждый кадр также несёт `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## Для кого это?

- **Вы запускаете долгие сессии агента** — миграции, наборы тестов, крупные рефакторинги — и то и дело заглядываете в терминал проверить, закончил он или завис.
- **Вы отходите от клавиатуры** — и хотите узнать в ту самую *секунду*, когда агент ждёт вашего подтверждения, а не через десять минут.
- **Вы используете Claude Code / Codex / agy / hermes** в headless-режиме и скучаете по наглядности полноценной IDE.
- **У вас есть GeekMagic SmallTV**, который простаивает, и вы хотите, чтобы он наконец приносил пользу.

Если вы когда-нибудь возвращались к терминалу и думали *"стоп, он что, всё это время меня ждал?"* — это для вас.

## Требования

- GeekMagic SmallTV с community-прошивкой **SD_RU / SD Pro** (ESP8266). Быстрая проверка — это должно вернуть JSON с массивом `files`:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  Официальная прошивка GeekMagic и "PRO" на базе ESP32 используют *другой* API и **не поддерживаются**.
  
- Устройство должно быть в той же Wi-Fi сети, что и эта машина.
- Python 3.8+ с Pillow (`pip install Pillow`).

## Установка

Распространяется через маркетплейс [`epicsagas/plugins`](https://github.com/epicsagas/plugins); сам плагин находится в [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

**Claude Code**

```bash
claude plugin marketplace add epicsagas/plugins
claude plugin install agent-glance@epicsagas
```

**Codex**

```bash
codex plugin marketplace add epicsagas/plugins
codex plugin add agent-glance@epicsagas
```

**agy (Antigravity)**

```bash
agy plugin install https://github.com/epicsagas/AgentGlance
```

**hermes**

```bash
hermes plugins install epicsagas/AgentGlance
hermes plugins enable agent-glance
```

### Что получает каждый хост

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | проверено полностью, end-to-end |
| Codex | ✅ | ✅ | ✅ | файл хуков соответствует задокументированной схеме; не проверено в рантайме |
| agy | ✅ | — | ✅ | формат хуков соответствует реально установленному плагину agy; не проверено в рантайме |
| hermes | ✅ | — | ❌ | только skills — hermes регистрируется через `register(ctx)`, без подключённых хуков жизненного цикла |

Затем настройте устройство — это найдёт его, сохранит IP, сделает резервную копию устройства и переключит его в режим монитора:

```
/agent-glance:setup
```

На хостах без слэш-команд выполните те же шаги вручную:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Хуки поставляются вместе с плагином и активируются сами. **Перезапустите агента после установки** — хуки загружаются при старте сессии.

## Настройка

Конфигурация читается **сначала из переменных окружения**, а при их отсутствии — из `~/.agent-glance/config.json` (записывается через `--ip`). Переменная окружения — более переносимый вариант для общих или многомашинных настроек.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | IP устройства — **обязательно** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | контекстное окно, используемое для масштабирования шкалы % | `200000` |
| `AGENT_GLANCE_PRESET` | пресет отображения: `default` \| `hosts` \| `anime` \| `custom` | `default` |
| `AGENT_GLANCE_LAYOUT` | макет режима gif: `frame` \| `fullscreen` | `frame` |

### Режим GIF и пресеты

По умолчанию используется статический кадр состояния, описанный выше. Выберите другой пресет, чтобы переключиться в **режим gif**, в котором скрипт компонует зацикленный анимированный GIF (персонаж в центре, шапка и нижний колонтитул статуса сохраняются), воспроизводимый локально на устройстве — одна загрузка на состояние, никакого сетевого трафика на каждый кадр. Состояние по-прежнему сигнализируется верхней акцентной полосой и цветом фона.

| Пресет | Что показывается |
|---|---|
| `default` | Статический кадр (исходное поведение) |
| `hosts` | Встроенный GIF-персонаж для каждого хоста в центре; шапка и колонтитул сохраняются |
| `anime` | *Зарезервировано* — слот существует, арт TBD; откатывается на персонажа hosts |
| `custom` | Ваши собственные GIF, по хосту и/или по состоянию (см. схему) |

Пресет выбирается через CLI-флаг `--preset` (сохраняется в `config.json`, как `--ip`):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` поставляется с нейтральными заглушками в `assets/hosts/`. Переопределите одну, положив `<host>.gif` в `~/.agent-glance/gifs/hosts/` (например, `claude-code.gif`, `codex.gif`, `antigravity.gif`, `hermes.gif`, `agent.gif`) — пользовательский файл имеет приоритет над встроенным.

`custom` читает `display.gifs` из `config.json`. Каждая запись хоста — это либо строка-путь (один GIF для всех состояний), либо карта по состояниям; `"default"` используется как запасной вариант. Любая запись также может быть `{"path": ..., "layout": "fullscreen"}`, чтобы развернуть её на весь экран:

```json
"display": {
  "preset": "custom",
  "layout": "frame",
  "gifs": {
    "default": "/abs/path/fallback.gif",
    "claude code": { "working": "a.gif", "waiting": "b.gif", "done": "c.gif" },
    "codex": "/one-gif-for-all-states.gif",
    "agent": { "path": "x.gif", "layout": "fullscreen" }
  }
}
```

Порядок разрешения при каждой отправке: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → встроенная заглушка hosts. Отсутствующий или нечитаемый GIF никогда не очищает экран — происходит откат к статическому кадру.

## Команды

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Полная настройка — обнаружение устройства, проверка прошивки, сохранение IP, резервное копирование, получение контроля |
| `/agent-glance:status` | Проверка состояния — доступность, активная тема, дублирующиеся хуки, лог ошибок |
| `/agent-glance:test` | Отправляет один кадр (или прогоняет все три) для проверки рендеринга |
| `/agent-glance:restore` | Возвращает устройство к исходным часам и фото |

Несколько опций доступны **только как CLI-флаги** (без слэш-команды) — они сохраняются в `~/.agent-glance/config.json` по аналогии с `--ip`:

| Flag | What it does |
|---|---|
| `--ip <IP>` | сохранить IP устройства |
| `--preset default\|hosts\|anime\|custom` | переключить режим отображения (см. [режим GIF](#режим-gif-и-пресеты)) |
| `--layout frame\|fullscreen` | макет режима gif (`frame` сохраняет шапку+колонтитул; `fullscreen` — только GIF) |
| `--test [state] [subtitle]` | отправить кадр; учитывает текущий пресет, так что предварительно показывает и режим gif |

## Как это работает

У этой прошивки **нет текстового API**, так что "печатать" в неё нечего. Вместо этого скрипт рендерит GIF 240×240 с помощью Pillow и загружает его в фотоальбом устройства, делая это изображение единственным включённым фото, а Photo — единственной включённой темой, так что кадр остаётся неизменным вместо переключения на другую тему. GIF-декодер прошивки также воспроизводит **анимированные** GIF, поэтому в режиме gif скрипт компонует многокадровый GIF, а устройство зацикливает его локально — одна загрузка на состояние, никакого трафика на каждый кадр.

```
host lifecycle hook (JSON on stdin)
        │
   scripts/agent_glance.py
     · normalises the payload  (hook_event_name | hookEventName)
     · maps the host's event to WORKING / APPROVAL / DONE
     · reads the session transcript for model / context / tokens
     · renders a 240×240 GIF (CJK-safe font fallback)
     · forks the upload so the agent never waits on the device
        │
   SmallTV photo album  →  display
```

## Хуки для нескольких хостов

Три хоста **не** используют общий формат хуков, поэтому у каждого свой файл. Общего `hooks/hooks.json` намеренно не существует — этот путь используется по умолчанию и Claude Code, и Codex, и если оставить файл там, его загрузит не тот хост.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | объявлен в `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | объявлен в `.codex-plugin/plugin.json` |
| agy | `hooks.json` (**корень** плагина) | вынужденно — схема манифеста agy имеет `additionalProperties:false`, поэтому путь нельзя объявить отдельно |

Поскольку у хостов разные жизненные циклы, события тоже различаются:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

И полезные нагрузки различаются: Claude Code и Codex отправляют `hook_event_name` / `transcript_path` (snake_case); agy отправляет `hookEventName` / `transcriptPath` (camelCase) и оборачивает свою конфигурацию в именованную группу хуков. Скрипт всё это нормализует.

Только Claude Code подставляет `${CLAUDE_PLUGIN_ROOT}` внутри команд хуков, поэтому два других хоста напрямую ссылаются на путь своего установленного плагина:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Справочник по API устройства (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Особенности, обнаруженные при исследовании реального устройства:

- `state` должен быть `1` / `0`. Прошивка выполняет над ним `atoi()`, так что `"true"` превращается в `0` и тихо делает противоположное задуманному.
- Отключение *последней* активной темы или фото возвращает **HTTP 403** — защита от пустого экрана. Настройка сначала включает целевой объект, а затем отключает остальные.
- ESP8266 однопоточный и возвращает 403, когда занят предыдущим запросом, поэтому загрузки повторяются.
- ⚠️ `/config` отдаёт пароль Wi-Fi устройства и ключ API погоды **в открытом виде и без какой-либо аутентификации**. Это поведение самой прошивки, а не то, что добавляет этот плагин — но в общей сети устройство следует считать недоверенным.

## Ограничения

- **7 тем устройства не могут каждая показывать отдельную сессию.** Только тема Photo отображает пользовательский контент; остальные шесть — фиксированные интерфейсы часов/погоды. Для смены нескольких сессий по кругу потребовалось бы несколько изображений в альбоме — это не реализовано.
- Метрики берутся из формата транскрипта Claude Code. В Codex/agy цвета состояния по-прежнему работают, но поля модели/токенов могут быть пустыми.
- Состояние (`config.json`, `device_backup.json`) хранится в `~/.agent-glance/`, а не в директории плагина, поэтому не стирается при обновлениях плагина.

## Лицензия

[MIT](../../../LICENSE)
