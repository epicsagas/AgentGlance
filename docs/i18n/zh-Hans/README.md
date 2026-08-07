<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | **[简体中文](README.md)** | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> 把 **GeekMagic SmallTV** 变成一块实时的智能体状态显示屏 —— 适用于 Claude Code、Codex 和 agy。

这块小屏幕会实时显示你的智能体正在做什么:**WORKING**、**APPROVAL NEEDED**、**DONE** —— 还会显示从实时会话记录中读取的模型、上下文窗口占用率和 token 数量。
最亮眼的功能是红色的 **APPROVAL** 屏幕:把它放在另一块显示器上,你就可以走开去做别的事,回头瞥一眼就能立刻知道它是否卡在等你确认,而不是十分钟后才发现。

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING**(琥珀色)+ 提示词 |
| approval needed | ⛔ **APPROVAL**(红色)+ 需要确认的内容 |
| turn finished | ✓ **DONE**(绿色) |

每一帧还会带上 `model · context bar + % · in/out tokens`。

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## 适合谁？

- **运行长时间 agent 会话的人** —— 数据迁移、测试套件、大型重构 —— 总忍不住切回终端看它到底是跑完了还是卡住了。
- **会离开键盘的人** —— 想在 agent 需要你批准的 *那一刻* 就知道，而不是十分钟后才发现。
- **以 headless 方式使用 Claude Code / Codex / agy / hermes**，却怀念完整 IDE 那种视觉反馈的人。
- **拥有一台 GeekMagic SmallTV** 却一直闲置、想让它真正派上用场的人。

如果你曾切回终端，心想 *"等等，它是不是一直在等我批准？"* —— 那这就是为你准备的。

## 环境要求

- 运行 **SD_RU / SD Pro** 社区固件(ESP8266)的 GeekMagic SmallTV。快速验证方法 —— 以下命令必须返回包含 `files` 数组的 JSON:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  GeekMagic 官方固件以及 ESP32 版的 "PRO" 使用 *不同* 的 API,**不受支持**。
  
- 设备需与本机连接同一个 Wi-Fi。
- Python 3.8+ 并安装 Pillow(`pip install Pillow`)。

## 安装

通过 [`epicsagas/plugins`](https://github.com/epicsagas/plugins) 市场发布,插件本体位于 [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance)。

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

### 各宿主平台的支持情况

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | 已完成端到端验证 |
| Codex | ✅ | ✅ | ✅ | 钩子文件与文档化的 schema 一致;尚未做运行时验证 |
| agy | ✅ | — | ✅ | 钩子格式与一个实际安装的 agy 插件一致;尚未做运行时验证 |
| hermes | ✅ | — | ❌ | 仅支持 skills —— hermes 只通过 `register(ctx)` 注册,没有接入生命周期钩子 |

接下来完成设备上线 —— 这会找到设备、保存 IP、备份设备,并切换到监视器模式:

```
/agent-glance:setup
```

在不支持斜杠命令的宿主上,手动执行相同的步骤:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

钩子随插件一起提供,会自行启用。**安装后请重启智能体** —— 钩子是在会话启动时加载的。

## 配置

配置**优先读取环境变量**,若不存在则回退到 `~/.agent-glance/config.json`(由 `--ip` 写入)。对于共享或多机环境,环境变量是更具可移植性的选择。

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | 设备 IP —— **必填** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | 用于缩放百分比条的上下文窗口大小 | `200000` |
| `AGENT_GLANCE_PRESET` | 显示预设：`default` \| `hosts` \| `anime` \| `custom` | `default` |
| `AGENT_GLANCE_LAYOUT` | gif 模式布局：`frame` \| `fullscreen` | `frame` |

### GIF 模式与预设

默认模式就是上文描述的静态状态帧。选择其他预设会切换到 **gif 模式**:脚本会合成一张循环播放的动画 GIF(角色居中,顶部 header 与底部状态 footer 保留),由设备在本地播放 —— 每个状态只上传一次,没有逐帧的网络流量。状态仍通过顶部的强调色条与背景色来指示。

| 预设 | 显示内容 |
|---|---|
| `default` | 静态帧(原有行为) |
| `hosts` | 中间显示自带的按宿主区分的角色 GIF,header + footer 保留 |
| `anime` | *预留* —— 槽位已留出,美术待定。回退到 hosts 的角色 |
| `custom` | 你自己的 GIF,可按宿主和/或按状态映射(见 schema) |

用 `--preset` CLI 标志选择预设(与 `--ip` 一样会持久化到 `config.json`):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` 在 `assets/hosts/` 中附带中性的占位图。把 `<host>.gif` 放到 `~/.agent-glance/gifs/hosts/` 即可覆盖某一个(例如 `claude-code.gif`、`codex.gif`、`antigravity.gif`、`hermes.gif`、`agent.gif`) —— 用户文件优先于自带文件。

### GIF 最佳规格与推荐参数

| 参数 | `frame` 布局 | `fullscreen` 布局 |
|---|---|---|
| **最佳分辨率** | **224 × 116 px** (宽高比约 1.93:1) 或 **116 × 116 px** (1:1 正方形) | **240 × 240 px** (1:1 正方形) |
| **合成目标区域** | 自动适应内嵌于 `MIDDLE_BOX = (8, 46, 224, 116)` | 覆盖 1.54 英寸 SmallTV 整个屏幕 |
| **推荐文件大小** | **100 KB – 300 KB** (最大 < 500 KB，以防止 ESP8266 RAM/OOM 崩溃) |
| **帧数** | **12 – 16 帧** (超出部分渲染器将自动抽帧降采样至 `_MAX_FRAMES = 16`) |
| **帧延迟** | **80ms – 150ms** / 帧 (1.2秒 – 2.0秒循环) |
| **调色板** | **64 – 128 色** (优化渲染速度与 Flash 闪存寿命) |

**将源 GIF 压缩到规格范围**(未处理的原始导出很容易达到几 MB):在整段素材中均匀采样帧,再以较短的目标循环重新编码,即使播放速度被压缩,完整的动作幅度依然保留。

1 — 按布局裁剪/缩放,从源文件中均匀采样约 14 帧:

```bash
# frame 布局:以信箱方式嵌入 MIDDLE_BOX,只需缩小即可(无需裁剪)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen 布局:会被拉伸填满 240x240,所以要先裁成正方形,否则会变形
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = 源文件帧数 ÷ 14(向下取整)— 用 ffprobe 获取源文件帧数(`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`)。

2 — 以较短的目标循环(10fps = 每帧 100ms ≈ 14 帧约 1.4 秒循环)和小调色板重新编码采样出的帧:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

还是超过 300 KB?先把 `max_colors` 降到 32(也可以试试 `dither=none`),再考虑减少帧数——真正拖累体积的是调色板,不是帧数。


`custom` 会读取 `config.json` 中的 `display.gifs`。每个 host 条目要么是一个路径字符串(所有状态共用同一张 GIF),要么是一张按状态映射的表;`"default"` 是回退项。任何条目也可以写成 `{"path": ..., "layout": "fullscreen"}`,让该条目单独以全屏方式显示:

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

每次推送时的解析顺序:`gifs[host][state]` → `gifs[host]` → `gifs["default"]` → 自带的 hosts 占位图。GIF 缺失或不可读时绝不会让屏幕变黑 —— 会回退到静态帧。

## 命令

| Command | What it does |
|---|---|
| `/agent-glance:setup` | 完整上线流程 —— 发现设备、验证固件、保存 IP、备份、接管控制 |
| `/agent-glance:status` | 健康检查 —— 可达性、当前主题、重复钩子、错误日志 |
| `/agent-glance:test` | 推送一帧(或依次循环三种状态)以检查渲染效果 |
| `/agent-glance:restore` | 把设备恢复到原来的时钟和照片状态 |

有几个选项**仅作为 CLI 标志**提供(没有对应的斜杠命令),它们与 `--ip` 一样持久化到 `~/.agent-glance/config.json`:

| 标志 | 作用 |
|---|---|
| `--ip <IP>` | 保存设备 IP |
| `--preset default\|hosts\|anime\|custom` | 切换显示模式(见 [GIF 模式](#gif-模式与预设)) |
| `--layout frame\|fullscreen` | gif 模式布局(`frame` 保留 header+footer;`fullscreen` 仅显示 GIF) |
| `--test [state] [subtitle]` | 推送一帧;遵循当前预设,因此也可用于预览 gif 模式 |

## 工作原理

该固件**没有文本 API**,所以根本没有可以"打印"的对象。脚本会改为用 Pillow 渲染一张 240×240 的 GIF,推送到设备的 Photo 相册中,并把这张图片设为唯一启用的照片、Photo 设为唯一启用的主题 —— 这样画面就会固定不变,不会被轮换掉。该固件的 GIF 解码器也能播放**动画** GIF,所以在 gif 模式下脚本会合成一张多帧 GIF,由设备在本地循环播放 —— 每个状态只上传一次,没有逐帧流量。

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

## 多宿主钩子

三个宿主平台**并不共用**同一套钩子格式,因此各自使用独立的文件。之所以刻意不放置通用的 `hooks/hooks.json`,是因为该路径同时是 Claude Code 和 Codex 的默认路径,留在那里会导致错误的宿主加载它。

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | 在 `.claude-plugin/plugin.json` 中声明 |
| Codex | `.codex-plugin/hooks.json` | 在 `.codex-plugin/plugin.json` 中声明 |
| agy | `hooks.json`(插件**根目录**) | 被迫如此 —— agy 的 manifest schema 是 `additionalProperties:false`,无法单独声明路径 |

由于各宿主的生命周期不同,对应的事件也不同:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

负载数据也不同:Claude Code 和 Codex 发送 `hook_event_name` / `transcript_path`(snake_case),agy 发送 `hookEventName` / `transcriptPath`(camelCase),并把配置包在一个带名字的钩子组里。脚本会把这些全部标准化。

只有 Claude Code 会在钩子命令中替换 `${CLAUDE_PLUGIN_ROOT}`,因此另外两个宿主直接引用各自已安装的插件路径:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## 设备 API 参考(SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

在实机上探测得到的坑:

- `state` 必须是 `1` / `0`。固件对它执行 `atoi()`,所以 `"true"` 会变成 `0`,悄无声息地做出与预期相反的动作。
- 关闭**最后一个**启用中的主题或照片会返回 **HTTP 403** —— 这是防止黑屏的保护机制。设置流程会先启用目标对象,再禁用其余的。
- ESP8266 是单线程的,处理前一个请求时会返回 403,所以上传会重试。
- ⚠️ `/config` 会在没有任何鉴权的情况下,以**明文**提供设备的 Wi-Fi 密码和天气 API 密钥。这是固件本身的行为,并非本插件新增的问题 —— 但在共享网络中,应将该设备视为不可信的。

## 局限性

- **7 个设备主题无法各自显示一个会话。** 只有 Photo 主题能渲染自定义内容,其余六个都是固定的时钟/天气界面。要轮流显示多个会话,就需要在相册里放多张图片 —— 目前尚未实现。
- 指标数据取自 Claude Code 的会话记录格式。在 Codex/agy 下状态颜色仍然可用,但模型/token 字段可能为空。
- 状态(`config.json`、`device_backup.json`)保存在 `~/.agent-glance/` 而非插件目录下,插件更新时也不会被清除。

## 许可证

[MIT](../../../LICENSE)
