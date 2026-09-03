<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | **[繁體中文](README.md)** | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> 把 **GeekMagic SmallTV** 變成一台即時代理狀態顯示器 —— 適用於 Claude Code、Codex 與 agy。

這台小螢幕會即時顯示你的代理目前正在做什麼:**WORKING**、**APPROVAL NEEDED**、**DONE** —— 並附上從即時工作階段紀錄中讀取的模型、上下文視窗使用率與 token 數量。
最亮眼的功能是紅色的 **APPROVAL** 畫面:把它放在另一台螢幕上,你就能先去做別的事,回頭瞥一眼就立刻知道它是否卡在等你確認,而不是十分鐘後才發現。

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING**(琥珀色)+ 提示詞 |
| approval needed | ⛔ **APPROVAL**(紅色)+ 需要確認的內容 |
| turn finished | ✓ **DONE**(綠色) |

每一幀都會附上 `model · context bar + % · in/out tokens`。

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## 適合誰？

- **執行長時間 agent 工作階段的人** —— 資料遷移、測試套件、大型重構 —— 總忍不住切回終端機看它到底是跑完了還是卡住了。
- **會離開鍵盤的人** —— 想在 agent 需要你批准的 *那一刻* 就知道，而不是十分鐘後才發現。
- **以 headless 方式使用 Claude Code / Codex / agy / hermes**，卻懷念完整 IDE 那種視覺回饋的人。
- **擁有一台 GeekMagic SmallTV** 卻一直閒置、想讓它真正派上用場的人。

如果你曾切回終端機，心想 *"等等，它是不是一直在等我批准？"* —— 那這就是為你準備的。

## 需求

- 運行任一受支援韌體的 GeekMagic SmallTV（`--ip` 儲存時自動偵測並記錄）：
  - **SD_RU / SD Pro** 社群韌體 (ESP8266) — 快速檢查 — 此指令應回傳包含 `files` 陣列的 JSON：

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra 原廠韌體** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — 快速檢查 — 此指令應回傳包含 `theme` 鍵的 JSON：

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  其他 GeekMagic 原廠韌體變體與 ESP32 "PRO" 使用*不同的* API，**不**受支援。

- 裝置需與此機器連線於同一個 Wi-Fi。
- Python 3.8+ 並安裝 Pillow(`pip install Pillow`)。

## 安裝

從本儲存庫獨立安裝 — 內建與外掛同名的 `agent-glance` 市集,無需中心市場。

**Grok Build (xAI)**

```bash
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

### 各主機平台的支援情況

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | 已完成端對端驗證 |
| Codex | ✅ | ✅ | ✅ | 掛鉤檔案與文件化的 schema 一致;尚未做執行期驗證 |
| agy | ✅ | — | ✅ | 掛鉤格式與一個實際安裝的 agy 外掛一致;尚未做執行期驗證 |
| hermes | ✅ | — | ❌ | 僅支援 skills —— hermes 只透過 `register(ctx)` 註冊,沒有接上生命週期掛鉤 |
| Grok Build | ✅ | ✅ | ✅ | 鉤子檔案遵循 Claude 相容架構；未經執行時驗證 |

接著完成裝置上線 —— 這會尋找裝置、儲存 IP、備份裝置,並切換到監視器模式:

```
/agent-glance:setup
```

在不支援斜線指令的主機上,請手動執行相同步驟:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

掛鉤隨外掛一併提供,會自行啟用。**安裝後請重新啟動代理** —— 掛鉤是在工作階段啟動時載入的。

## 設定

設定會**優先讀取環境變數**,若不存在則退回 `~/.agent-glance/config.json`(由 `--ip` 寫入)。若是共用或多台機器的環境,環境變數是可攜性較高的選擇。

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | 裝置 IP —— **必填** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | 用於縮放百分比條的上下文視窗大小 | `200000` |
| `AGENT_GLANCE_PRESET` | 顯示預設:`default` | `hosts` | `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | gif 模式版面:`frame` | `fullscreen` | `frame` |

### GIF 模式與預設

> [!WARNING]
> **GIF 檔案容量注意事項**: 過大的 GIF 檔案會對裝置記憶體（ESP8266 RAM/Flash）造成巨大負擔，可能導致意外重啟或崩潰。請務必將檔案保持在 **< 100 KB** 以內。

預設模式為靜態畫面。選擇其他預設會切換到 gif 模式,此模式會合成一張循環播放的動態 GIF(角色置中,並保留頁首 header 與狀態頁尾 footer),由裝置在本機播放 —— 每個狀態只需上傳一次,沒有逐幀的流量。狀態仍由頂部的強調條與背景顏色來指示。

| Preset | 顯示內容 |
|---|---|
| `default` | 靜態畫面(原始行為) |
| `hosts` | 中央播放隨附的各主機角色 GIF,保留頁首與頁尾 |
| `custom` | 你自備的 GIF,可按主機和/或按狀態指定(詳見 schema) |

```
python3 scripts/agent_glance.py --preset hosts
```

`--preset` 會像 `--ip` 一樣持久化寫入 `config.json`。

`hosts` 在 `assets/gif/` 中隨附中性的預留素材;覆蓋方式為將 `<host>.gif` 放進 `~/.agent-glance/gifs/hosts/`(例如 `claude-code.gif`、`codex.gif`、`antigravity.gif`、`hermes.gif`、`agent.gif`)—— 使用者檔案優先於隨附素材。

### GIF 最佳規格與推薦參數

| 參數 | `frame` 佈局 | `fullscreen` 佈局 |
|---|---|---|
| **最佳解析度** | **224 × 116 px** (長寬比約 1.93:1) 或 **116 × 116 px** (1:1 正方形) | **240 × 240 px** (1:1 正方形) |
| **合成目標區域** | 自動適應內嵌於 `MIDDLE_BOX = (8, 46, 224, 116)` | 覆蓋 1.54 吋 SmallTV 整個螢幕 |
| **推薦檔案大小** | **< 100 KB** (硬性上限 < 300 KB，以防止 ESP8266 RAM/OOM 崩潰及重啟) |
| **影格數** | **12 – 16 影格** (超出部分算色器將自動抽幀降採樣至 `_MAX_FRAMES = 16`) |
| **影格延遲** | **80ms – 150ms** / 影格 (1.2秒 – 2.0秒循環) |
| **調色板** | **64 – 128 色** (優化算色速度與 Flash 快閃記憶體壽命) |

**將來源 GIF 壓縮到規格範圍**(未處理的原始匯出很容易達到數 MB):在整段素材中均勻取樣影格,再以較短的目標循環重新編碼,即使播放速度被壓縮,完整的動作幅度仍會保留。

1 — 依佈局裁切/縮放,從來源均勻取樣約 14 個影格:

```bash
# frame 佈局:以信箱方式嵌入 MIDDLE_BOX,只需縮小即可(不需裁切)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen 佈局:會被拉伸填滿 240x240,所以要先裁成正方形,否則會變形
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = 來源影格數 ÷ 14(無條件捨去)— 用 ffprobe 取得來源影格數(`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`)。

2 — 以較短的目標循環(10fps = 每格 100ms ≈ 14 格約 1.4 秒循環)與小調色板重新編碼取樣出的影格:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

仍超過 300 KB?先把 `max_colors` 降到 32(也可試試 `dither=none`),再考慮減少影格數——真正影響體積的是調色板。


`custom` 會從 `config.json` 讀取 `display.gifs`;每個 host 條目可為路徑字串(所有狀態共用一張 GIF)或按狀態的對應表;`"default"` 為後備;任何條目都可為 `{"path":...,"layout":"fullscreen"}`。

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

每次推送時的解析順序:`gifs[host][state]` → `gifs[host]` → `gifs["default"]` → 隨附的 hosts 預留素材。GIF 若缺失或無法讀取,絕不會讓畫面空白 —— 會退回為靜態畫面。

## 指令

| Command | What it does |
|---|---|
| `/agent-glance:setup` | 完整上線流程 —— 尋找裝置、驗證韌體、儲存 IP、備份、取得控制權 |
| `/agent-glance:status` | 健康檢查 —— 連線可達性、目前主題、重複掛鉤、錯誤紀錄 |
| `/agent-glance:test` | 推送一幀(或依序循環三種狀態)以檢查渲染效果 |
| `/agent-glance:theme` | 快速查看裝置自帶畫面 — 天氣、預報、時鐘（Ultra 專用；下次活動時監視器自動恢復） |
| `/agent-glance:restore` | 將裝置還原為原本的時鐘與相片狀態 |

有少數選項僅為 CLI 旗標(沒有對應的斜線指令),會像 `--ip` 一樣持久化寫入 `~/.agent-glance/config.json`。

| Flag | 功能 |
|---|---|
| `--ip <IP>` | 儲存裝置 IP |
| `--preset default\|hosts\|custom` | 切換顯示模式(詳見 [GIF 模式](#gif-模式與預設)) |
| `--layout frame\|fullscreen` | gif 模式版面(frame 保留頁首與頁尾;fullscreen 僅顯示 GIF) |
| `--test [state] [subtitle]` | 推送一幀;遵循目前預設,因此可預覽 gif 模式 |

## 運作原理

此韌體**沒有文字 API**,因此根本沒有可以「輸出」的對象。腳本改為用 Pillow 渲染一張 240×240 的 GIF,推送到裝置的 Photo 相簿中,並將該圖片設為唯一啟用的相片、Photo 設為唯一啟用的主題 —— 讓畫面固定不變,不會被輪替掉。韌體的 GIF 解碼器也會播放**動態** GIF,因此在 gif 模式下,腳本會合成一張多幀 GIF,由裝置在本機循環播放 —— 每個狀態只需上傳一次,沒有逐幀的流量。

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

## 多主機掛鉤

三個主機平台**並未共用**同一套掛鉤格式,因此各自使用獨立的檔案。之所以刻意不放置通用的 `hooks/hooks.json`,是因為該路徑同時是 Claude Code 與 Codex 的預設路徑,留在那裡會導致錯誤的主機載入它。

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | 於 `.claude-plugin/plugin.json` 中宣告 |
| Codex | `.codex-plugin/hooks.json` | 於 `.codex-plugin/plugin.json` 中宣告 |
| agy | `hooks.json`(外掛**根目錄**) | 被迫如此 —— agy 的 manifest schema 為 `additionalProperties:false`,無法單獨宣告路徑 |

由於各主機的生命週期不同,對應的事件也不同:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

酬載資料也不同:Claude Code 與 Codex 傳送 `hook_event_name` / `transcript_path`(snake_case),agy 傳送 `hookEventName` / `transcriptPath`(camelCase),並將設定包在一個具名的掛鉤群組裡。腳本會將這一切正規化。

只有 Claude Code 會在掛鉤指令中替換 `${CLAUDE_PLUGIN_ROOT}`,因此另外兩個主機直接參照各自已安裝的外掛路徑:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## 裝置 API 參考(SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

在實機上測試發現的注意事項:

- `state` 必須是 `1` / `0`。韌體會對它執行 `atoi()`,所以 `"true"` 會變成 `0`,悄悄做出與預期相反的動作。
- 關閉**最後一個**啟用中的主題或相片會回傳 **HTTP 403** —— 這是避免畫面全黑的保護機制。設定流程會先啟用目標對象,再停用其餘的。
- ESP8266 為單執行緒,處理前一個請求時會回傳 403,因此上傳會重試。
- ⚠️ `/config` 會在沒有任何驗證的情況下,以**明文**提供裝置的 Wi-Fi 密碼與天氣 API 金鑰。這是韌體本身的行為,並非本外掛新增的問題 —— 但在共用網路中,應將此裝置視為不可信任的。

## 裝置 API 參考（SmallTV Ultra 原廠韌體）

主題：1 今日天氣時鐘 · 2 天氣預報 · **3 相簿** · 4–6 時鐘樣式 · 7 簡易天氣時鐘。

| Action | Endpoint |
|---|---|
| 上傳圖片 | `POST /doUpload?dir=/image/` (multipart 欄位 `image`；同名重傳會覆寫) |
| 固定到畫面 | `GET /set?img=/image/<f>` (URL 編碼；需要主題 3) |
| 切換主題 | `GET /set?theme=<n>` |
| 主題開關 | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| 刪除檔案 | `GET /delete?file=/image/<f>` |
| 讀取狀態 | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

實測真機時發現的注意點：

- 顯示的圖片由 `/set?img=` *固定* — 相簿其他檔案保留但不會輪播（沒有 SD_RU 那樣的單圖啟用旗標；setup 不會動它們）。
- 動圖在裝置本機解碼並循環；整個 3 MB 檔案系統與天氣/時鐘資源共享，請保持 GIF 小（原廠約剩 1 MB）。
- `/set?img=` 與 `/set?theme=` 回傳字面文字 `OK`，不是 JSON。
- ⚠️ 與 SD_RU 相同的信任模型：所有端點在區域網路內無認證。

## 限制

- **7 個裝置主題無法各自顯示一個工作階段。** 只有 Photo 主題能呈現自訂內容,其餘六個都是固定的時鐘/天氣介面。要輪流顯示多個工作階段,就需要在相簿中放多張圖片 —— 目前尚未實作。
- 指標資料取自 Claude Code 的工作階段紀錄格式。在 Codex/agy 下狀態顏色仍可運作,但模型/token 欄位可能是空的。
- 狀態(`config.json`、`device_backup.json`)儲存在 `~/.agent-glance/` 而非外掛目錄下,外掛更新時也不會被清除。

## 授權

[MIT](../../../LICENSE)
