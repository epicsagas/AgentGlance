<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | **[한국어](README.md)** | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<center>
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</center>

> **GeekMagic SmallTV**를 실시간 에이전트 상태 디스플레이로 바꿔줍니다 — Claude Code, Codex, agy용.

작은 TV 화면에 지금 에이전트가 무엇을 하고 있는지 보여줍니다: **WORKING**, **APPROVAL NEEDED**, **DONE** — 그리고 라이브 세션 트랜스크립트에서 가져온 모델, 컨텍스트 윈도우 사용량, 토큰 수까지 함께 표시합니다.
가장 강력한 기능은 빨간색 **APPROVAL** 화면입니다: 에이전트를 다른 모니터에 띄워두면, 자리를 비웠다가도 힐끗 보는 것만으로 10분 뒤에야 알아채는 대신 바로 그 순간 승인 대기 중임을 알 수 있습니다.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (호박색) + 프롬프트 |
| approval needed | ⛔ **APPROVAL** (빨간색) + 요청 내용 |
| turn finished | ✓ **DONE** (초록색) |

각 화면에는 `model · context bar + % · in/out tokens`도 함께 표시됩니다.

<center>
<img width="49%" src="../../../assets/claude-approval.jpeg" alter="claude approval">
<img width="49%" src="../../../assets/claude-done.jpeg" alter="claude approval">
</center>

## 요구 사항

- **SD_RU / SD Pro** 커뮤니티 펌웨어(ESP8266)가 설치된 GeekMagic SmallTV. 간단 확인 — 아래 명령이 `files` 배열을 포함한 JSON을 반환해야 합니다:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  GeekMagic 정식 펌웨어와 ESP32 기반 "PRO"는 *다른* API를 사용하며 **지원하지 않습니다**.
  
- 기기가 이 머신과 동일한 Wi-Fi에 연결되어 있어야 합니다.
- Pillow가 설치된 Python 3.8+ (`pip install Pillow`).

## 설치

[`epicsagas/plugins`](https://github.com/epicsagas/plugins) 마켓플레이스로 배포되며, 플러그인 본체는 [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance)에 있습니다.

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

### 호스트별 지원 범위

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | 엔드투엔드 검증 완료 |
| Codex | ✅ | ✅ | ✅ | 훅 파일이 문서화된 스키마와 일치함; 런타임 미검증 |
| agy | ✅ | — | ✅ | 실제 설치된 agy 플러그인과 훅 형식이 일치함; 런타임 미검증 |
| hermes | ✅ | — | ❌ | 스킬만 지원 — hermes는 `register(ctx)`로 등록할 뿐, 생명주기 훅은 연결되어 있지 않음 |

그다음 기기 온보딩을 진행합니다 — 기기를 찾고, IP를 저장하고, 기기를 백업한 뒤 모니터 모드로 전환합니다:

```
/agent-glance:setup
```

슬래시 명령을 지원하지 않는 호스트에서는 같은 과정을 직접 실행하세요:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

훅은 플러그인에 포함되어 있으며 자동으로 활성화됩니다. **설치 후에는 에이전트를 재시작하세요** — 훅은 세션 시작 시점에 로드됩니다.

## 설정

설정은 **환경 변수를 우선** 읽고, 없으면 `~/.agent-glance/config.json`(`--ip`로 기록됨)으로 대체됩니다. 여러 머신에서 공유하는 환경이라면 환경 변수 쪽이 이식성이 더 좋습니다.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | 기기 IP — **필수** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | 퍼센트 바 스케일링에 쓰이는 컨텍스트 윈도우 크기 | `200000` |

## 명령어

| Command | What it does |
|---|---|
| `/agent-glance:setup` | 전체 온보딩 — 기기 탐색, 펌웨어 확인, IP 저장, 백업, 제어권 확보 |
| `/agent-glance:status` | 상태 점검 — 연결 가능 여부, 활성 테마, 중복 훅, 에러 로그 |
| `/agent-glance:test` | 프레임 하나(또는 세 가지 모두)를 전송해 렌더링 확인 |
| `/agent-glance:restore` | 기기를 원래의 시계·사진 상태로 되돌림 |

## 동작 원리

이 펌웨어에는 **텍스트 API가 없어서**, "출력"할 대상 자체가 없습니다. 대신 스크립트가 Pillow로 240×240 GIF를 렌더링해 기기의 Photo 앨범에 넣고, 그 이미지를 유일하게 활성화된 사진으로, Photo를 유일하게 활성화된 테마로 만들어 — 화면이 다른 테마로 돌아가지 않고 고정되도록 합니다.

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

## 멀티호스트 훅

세 호스트는 훅 형식을 공유하지 **않으므로** 각각 별도의 파일을 사용합니다. 공용 `hooks/hooks.json`이 의도적으로 존재하지 않는 이유는 — 그 경로가 Claude Code와 Codex *모두*의 기본 경로라서, 그대로 두면 엉뚱한 호스트가 그 파일을 읽어버리기 때문입니다.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | `.claude-plugin/plugin.json`에 선언됨 |
| Codex | `.codex-plugin/hooks.json` | `.codex-plugin/plugin.json`에 선언됨 |
| agy | `hooks.json` (플러그인 **루트**) | 강제됨 — agy의 매니페스트 스키마가 `additionalProperties:false`라 경로를 따로 선언할 수 없음 |

호스트마다 생명주기가 다르기 때문에 이벤트도 다릅니다:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

페이로드도 다릅니다: Claude Code와 Codex는 `hook_event_name` / `transcript_path`(스네이크 케이스)를 보내고, agy는 `hookEventName` / `transcriptPath`(카멜 케이스)를 보내며 설정을 이름이 붙은 훅 그룹으로 감쌉니다. 스크립트가 이 모든 것을 정규화합니다.

훅 명령 안에서 `${CLAUDE_PLUGIN_ROOT}`를 치환하는 것은 Claude Code뿐이라, 나머지 둘은 설치된 플러그인 경로를 직접 참조합니다:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## 기기 API 레퍼런스 (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

실제 기기를 조사하며 발견한 주의사항:

- `state`는 반드시 `1` / `0`이어야 합니다. 펌웨어가 여기에 `atoi()`를 실행하기 때문에 `"true"`는 `0`이 되어, 의도한 것과 정반대로 조용히 동작합니다.
- 마지막으로 남은 활성 테마나 사진을 끄면 **HTTP 403**이 반환됩니다 — 화면이 완전히 비는 것을 막는 가드입니다. 설정 과정은 목표 대상을 먼저 활성화한 뒤 나머지를 비활성화합니다.
- ESP8266은 싱글 스레드라 이전 요청 처리 중에는 403을 반환하므로, 업로드는 재시도합니다.
- ⚠️ `/config`는 인증 없이 기기의 **Wi-Fi 비밀번호와 날씨 API 키를 평문으로** 제공합니다. 이는 이 플러그인이 추가한 것이 아니라 펌웨어 자체의 동작입니다 — 다만 공유 네트워크에서는 이 기기를 신뢰할 수 없는 것으로 취급하세요.

## 한계

- **7개의 기기 테마가 각각 세션을 표시할 수는 없습니다.** 커스텀 콘텐츠를 렌더링하는 것은 Photo 테마뿐이며, 나머지 6개는 고정된 시계/날씨 UI입니다. 여러 세션을 순환 표시하려면 앨범에 이미지가 여러 개 있어야 하는데, 아직 구현되어 있지 않습니다.
- 지표는 Claude Code의 트랜스크립트 형식에서 가져옵니다. Codex/agy에서도 상태 색상은 동작하지만, 모델/토큰 필드는 비어 있을 수 있습니다.
- 상태(`config.json`, `device_backup.json`)는 플러그인 디렉터리가 아니라 `~/.agent-glance/`에 저장되며, 이 디렉터리는 플러그인 업데이트 시에도 지워지지 않습니다.

## 라이선스

[MIT](../../../LICENSE)
