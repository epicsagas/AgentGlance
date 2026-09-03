<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | **[한국어](README.md)** | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> **GeekMagic SmallTV**를 실시간 에이전트 상태 디스플레이로 바꿔줍니다 — Claude Code, Codex, agy용.

작은 TV 화면에 지금 에이전트가 무엇을 하고 있는지 보여줍니다: **WORKING**, **APPROVAL NEEDED**, **DONE** — 그리고 라이브 세션 트랜스크립트에서 가져온 모델, 컨텍스트 윈도우 사용량, 토큰 수까지 함께 표시합니다.
가장 강력한 기능은 빨간색 **APPROVAL** 화면입니다: 에이전트를 다른 모니터에 띄워두면, 자리를 비웠다가도 힐끗 보는 것만으로 10분 뒤에야 알아채는 대신 바로 그 순간 승인 대기 중임을 알 수 있습니다.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (호박색) + 프롬프트 |
| approval needed | ⛔ **APPROVAL** (빨간색) + 요청 내용 |
| turn finished | ✓ **DONE** (초록색) |

각 화면에는 `model · context bar + % · in/out tokens`도 함께 표시됩니다.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## 누구에게 유용한가요?

- **오래 걸리는 에이전트 세션을 실행하는 분** — 마이그레이션, 테스트 스위트, 대규모 리팩터링 등 — 끝났는지 멈췄는지 확인하려고 터미널을 자꾸 들여다보게 된다면.
- **자리를 비우는 분** — 에이전트가 승인을 기다리는 *순간*을, 열 분 뒤가 아니라 바로 알고 싶다면.
- **Claude Code / Codex / agy / hermes를 헤드리스로 쓰면서** 풀 IDE가 주는 시각적 피드백이 그리운 분.
- **GeekMagic SmallTV를 가지고 계신데** 방치 중이고, 제 몫을 하게 만들고 싶으신 분.

터미널로 돌아가 *"잠깐, 이걸 내 승인을 기다리느라 계속 멈춰 있었어?"*라고 생각해 본 적이 있다면 — 이 플러그인은 당신을 위한 겁니다.

## 요구 사항

- 다음 지원 펌웨어 중 하나를 실행하는 GeekMagic SmallTV(`--ip` 저장 시 자동 감지되어 기록):
  - **SD_RU / SD Pro** 커뮤니티 펌웨어 (ESP8266) — 간단 확인 — 이 명령은 `files` 배열을 포함한 JSON을 반환해야 합니다:

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra 정식 펌웨어** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — 간단 확인 — 이 명령은 `theme` 키를 포함한 JSON을 반환해야 합니다:

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  그 외 GeekMagic 정식 펌웨어 변형과 ESP32 "PRO"는 *다른* API를 사용하며 **지원하지 않습니다**.

- 기기가 이 머신과 동일한 Wi-Fi에 연결되어 있어야 합니다.
- Pillow가 설치된 Python 3.8+ (`pip install Pillow`).

## 설치

이 레포지토리에서 단독 설치 — 플러그인과 동일한 이름의 `agent-glance` 마켓플레이스를 포함합니다. 허브 불필요.

**Grok Build (xAI)**

```bash
grok plugin marketplace add epicsagas/AgentGlance
grok plugin install epicsagas/AgentGlance --trust
```

**Claude Code**

```bash
claude plugin marketplace add epicsagas/AgentGlance
claude plugin install agent-glance@agent-glance
```

**Codex**

```bash
codex plugin marketplace add epicsagas/AgentGlance
codex plugin add agent-glance@agent-glance
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
| Grok Build | ✅ | ✅ | ✅ | 훅 파일이 Claude 호환 스키마를 따름; 런타임 미검증 |

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
| `AGENT_GLANCE_PRESET` | 화면 프리셋: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | gif 모드 레이아웃: `frame` \| `fullscreen` | `frame` |

### GIF 모드와 프리셋

> [!WARNING]
> **GIF 용량 관련 주의사항**: GIF 용량이 너무 크면 기기 메모리(ESP8266 RAM/Flash)에 과도한 부하가 걸려 재부팅(Reboot)되는 등 기기가 불안정해질 수 있습니다. 아래 권장 사양(**100 KB 미만**)을 반드시 지켜주세요.

기본 모드는 위에서 설명한 정적 상태 프레임입니다. 다른 프리셋을 선택하면 **gif 모드**로 전환되어, 중간에 캐릭터가 들어가고 헤더와 상태 푸터는 유지한 채 루프 애니메이션 GIF를 합성합니다. 기기가 이를 로컬에서 재생하므로 상태별로 업로드는 한 번이고 프레임별 네트워크 트래픽은 없습니다. 상태는 상단 액센트 바 + 배경색으로 여전히 표시됩니다.

| 프리셋 | 표시 내용 |
|---|---|
| `default` | 정적 프레임 (기존 동작) |
| `hosts` | 번들된 호스트별 캐릭터 GIF를 중간에 표시, 헤더·푸터 유지 |
| `custom` | 사용자 지정 GIF, 호스트별/상태별 매핑 (스키마 참고) |

프리셋은 `--preset` CLI 플래그로 선택합니다 (`--ip`처럼 `config.json`에 저장됨):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts`는 `assets/gif/`에 중립 플레이스홀더를 기본 제공하므로 바로 동작합니다. 직접 캐릭터를 쓰려면 GIF 파일을 사용자 디렉터리에 넣으세요 — 번들 파일보다 우선 적용되며, 다음 상태 푸시 때 화면에 반영됩니다 (재시작 불필요):

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp 내캐릭터.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

파일명은 바꿀 호스트 이름으로 (소문자, 공백 → 하이픈):

| 감지된 호스트 | 오버라이드 파일명 |
|---|---|
| Claude Code | `claude-code.gif` |
| Codex | `codex.gif` |
| Antigravity | `antigravity.gif` |
| Hermes | `hermes.gif` |
| 그 외 호스트 | `agent.gif` |

### GIF 최적 규격 및 권장 사양

| 항목 | `frame` 레이아웃 | `fullscreen` 레이아웃 |
|---|---|---|
| **최적 해상도** | **224 × 116 px** (비율 ~1.93:1) 또는 **116 × 116 px** (1:1) | **240 × 240 px** (1:1 정사각형) |
| **합성 영역** | `MIDDLE_BOX = (8, 46, 224, 116)` 내부 맞춤 | SmallTV 1.54인치 전체 화면 덮음 |
| **권장 파일 용량** | **100 KB 미만** (ESP8266 RAM/OOM 방지 및 기기 재부팅 예방을 위해 최대 300 KB 미만) |
| **프레임 수** | **12 – 16 프레임** (렌더러에서 `_MAX_FRAMES = 16`으로 자동 다운샘플링) |
| **프레임 딜레이** | **80ms – 150ms** / 프레임당 (1.2초 – 2.0초 루프) |
| **색상 팔레트** | **64 – 128 Colors** (렌더링 속도 최적화 및 플래시 메모리 보호) |

**원본 GIF를 스펙에 맞게 줄이기** (가공 전 원본은 쉽게 수 MB를 넘음): 전체 구간에서 프레임을 고르게 샘플링한 뒤 짧은 목표 루프로 재인코딩하면, 재생 속도는 압축돼도 동작 범위는 그대로 살아남는다.

1 — 레이아웃에 맞춰 크롭/스케일하면서 원본에서 ~14프레임을 고르게 샘플링:

```bash
# frame 레이아웃: MIDDLE_BOX 안에 레터박스로 들어가므로 그냥 축소만 하면 됨 (크롭 불필요)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen 레이아웃: 240x240으로 늘려 채우므로 먼저 정사각형으로 크롭 안 하면 찌그러짐
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = 원본 프레임 수 ÷ 14 (내림) — ffprobe로 확인 (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`).

2 — 샘플링한 프레임을 짧은 목표 루프(10fps = 프레임당 100ms ≈ 14프레임 기준 1.4초 루프)와 작은 팔레트로 재인코딩:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

그래도 300 KB 넘으면, 프레임 수 줄이기 전에 `max_colors`를 32로 낮춰라 (`dither=none`도 시도) — 루프 용량을 실제로 좌우하는 건 그쪽이다.



`custom`은 `config.json`의 `display.gifs`를 읽습니다. 각 호스트 항목은 경로 문자열(모든 상태에 동일한 GIF)이거나 상태별 맵이며, `"default"`는 폴백입니다. 각 항목은 `{"path": ..., "layout": "fullscreen"}` 형태로 해당 항목만 전체화면으로 지정할 수도 있습니다:

```json
"display": {
  "preset": "custom",
  "layout": "frame",
  "gifs": {
    "default": "/절대경로/fallback.gif",
    "claude code": { "working": "a.gif", "waiting": "b.gif", "done": "c.gif" },
    "codex": "/모든-상태-동일.gif",
    "agent": { "path": "x.gif", "layout": "fullscreen" }
  }
}
```

푸시 시 해석 순서: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → 번들 hosts 플레이스홀더. 없거나 읽을 수 없는 GIF는 화면을 비우지 않고 정적 프레임으로 폴백합니다.

## 명령어

| Command | What it does |
|---|---|
| `/agent-glance:setup` | 전체 온보딩 — 기기 탐색, 펌웨어 확인, IP 저장, 백업, 제어권 확보 |
| `/agent-glance:status` | 상태 점검 — 연결 가능 여부, 활성 테마, 중복 훅, 에러 로그 |
| `/agent-glance:test` | 프레임 하나(또는 세 가지 모두)를 전송해 렌더링 확인 |
| `/agent-glance:theme` | 기기 자체 화면 잠깐 보기 — 날씨, 예보, 시계 (Ultra; 모니터는 다음 활동 시 자동 복귀) |
| `/agent-glance:restore` | 기기를 원래의 시계·사진 상태로 되돌림 |

일부 옵션은 **CLI 플래그 전용**입니다 (슬래시 명령어 없음). `--ip`처럼 `~/.agent-glance/config.json`에 저장됩니다:

| 플래그 | 동작 |
|---|---|
| `--ip <IP>` | 기기 IP 저장 |
| `--preset default\|hosts\|custom` | 화면 모드 전환 ([GIF 모드](#gif-모드와-프리셋) 참고) |
| `--layout frame\|fullscreen` | gif 모드 레이아웃 (`frame`은 헤더+푸터 유지, `fullscreen`은 GIF만) |
| `--test [state] [subtitle]` | 프레임 전송, 현재 프리셋을 따르므로 gif 모드 미리보기에도 쓰임 |

## 동작 원리

이 펌웨어에는 **텍스트 API가 없어서**, "출력"할 대상 자체가 없습니다. 대신 스크립트가 Pillow로 240×240 GIF를 렌더링해 기기의 Photo 앨범에 넣고, 그 이미지를 유일하게 활성화된 사진으로, Photo를 유일하게 활성화된 테마로 만들어 — 화면이 다른 테마로 돌아가지 않고 고정되도록 합니다. 이 펌웨어의 GIF 디코더는 **애니메이션** GIF도 재생하므로, gif 모드에서는 멀티프레임 GIF를 합성해 기기가 로컬에서 루프로 재생합니다 — 상태별 업로드 한 번, 프레임별 트래픽은 없습니다.

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

## 기기 API 레퍼런스 (SmallTV Ultra 정식 펌웨어)

테마: 1 오늘 날씨 시계 · 2 날씨 예보 · **3 사진 앨범** · 4–6 시계 스타일 · 7 심플 시계.

| Action | Endpoint |
|---|---|
| 이미지 업로드 | `POST /doUpload?dir=/image/` (multipart 필드 `image`; 같은 이름 재업로드 시 덮어씀) |
| 화면 고정 | `GET /set?img=/image/<f>` (URL 인코딩; 테마 3 필요) |
| 테마 전환 | `GET /set?theme=<n>` |
| 테마 플래그 | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| 파일 삭제 | `GET /delete?file=/image/<f>` |
| 상태 읽기 | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

실제 기기 프로빙으로 발견한 주의점:

- 표시 이미지는 `/set?img=`로 *고정*됩니다 — 앨범의 나머지 파일은 남지만 절대 순환하지 않습니다(SD_RU 같은 사진별 활성 플래그가 없고, setup은 이를 건드리지 않습니다).
- 애니메이션 GIF는 기기에서 디코딩·루프됩니다. 3MB 파일시스템 전체를 날씨/시계 에셋과 공유하므로 GIF는 작게 유지하세요(정션 기기 약 1MB 여유).
- `/set?img=`, `/set?theme=`는 JSON이 아니라 리터럴 텍스트 `OK`를 반환합니다.
- ⚠️ SD_RU와 동일한 신뢰 수준: 모든 엔드포인트가 LAN에서 인증 없이 열려 있습니다.

## 한계

- **7개의 기기 테마가 각각 세션을 표시할 수는 없습니다.** 커스텀 콘텐츠를 렌더링하는 것은 Photo 테마뿐이며, 나머지 6개는 고정된 시계/날씨 UI입니다. 여러 세션을 순환 표시하려면 앨범에 이미지가 여러 개 있어야 하는데, 아직 구현되어 있지 않습니다.
- 지표는 Claude Code의 트랜스크립트 형식에서 가져옵니다. Codex/agy에서도 상태 색상은 동작하지만, 모델/토큰 필드는 비어 있을 수 있습니다.
- 상태(`config.json`, `device_backup.json`)는 플러그인 디렉터리가 아니라 `~/.agent-glance/`에 저장되며, 이 디렉터리는 플러그인 업데이트 시에도 지워지지 않습니다.

## 라이선스

[MIT](../../../LICENSE)
