<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | **[繁體中文](README.md)** | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<center>
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</center>

> 把 **GeekMagic SmallTV** 變成一台即時代理狀態顯示器 —— 適用於 Claude Code、Codex 與 agy。

這台小螢幕會即時顯示你的代理目前正在做什麼:**WORKING**、**APPROVAL NEEDED**、**DONE** —— 並附上從即時工作階段紀錄中讀取的模型、上下文視窗使用率與 token 數量。
最亮眼的功能是紅色的 **APPROVAL** 畫面:把它放在另一台螢幕上,你就能先去做別的事,回頭瞥一眼就立刻知道它是否卡在等你確認,而不是十分鐘後才發現。

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING**(琥珀色)+ 提示詞 |
| approval needed | ⛔ **APPROVAL**(紅色)+ 需要確認的內容 |
| turn finished | ✓ **DONE**(綠色) |

每一幀都會附上 `model · context bar + % · in/out tokens`。

<center>
<img width="49%" src="../../../assets/claude-approval.jpeg" alter="claude approval">
<img width="49%" src="../../../assets/claude-done.jpeg" alter="claude approval">
</center>

## 需求

- 執行 **SD_RU / SD Pro** 社群韌體(ESP8266)的 GeekMagic SmallTV。快速驗證方式 —— 以下指令必須回傳含有 `files` 陣列的 JSON:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  GeekMagic 原廠韌體與 ESP32 版的「PRO」使用 *不同* 的 API,**不受支援**。
  
- 裝置需與此機器連線於同一個 Wi-Fi。
- Python 3.8+ 並安裝 Pillow(`pip install Pillow`)。

## 安裝

透過 [`epicsagas/plugins`](https://github.com/epicsagas/plugins) 市集發佈,外掛本體位於 [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance)。

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

### 各主機平台的支援情況

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | 已完成端對端驗證 |
| Codex | ✅ | ✅ | ✅ | 掛鉤檔案與文件化的 schema 一致;尚未做執行期驗證 |
| agy | ✅ | — | ✅ | 掛鉤格式與一個實際安裝的 agy 外掛一致;尚未做執行期驗證 |
| hermes | ✅ | — | ❌ | 僅支援 skills —— hermes 只透過 `register(ctx)` 註冊,沒有接上生命週期掛鉤 |

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

## 指令

| Command | What it does |
|---|---|
| `/agent-glance:setup` | 完整上線流程 —— 尋找裝置、驗證韌體、儲存 IP、備份、取得控制權 |
| `/agent-glance:status` | 健康檢查 —— 連線可達性、目前主題、重複掛鉤、錯誤紀錄 |
| `/agent-glance:test` | 推送一幀(或依序循環三種狀態)以檢查渲染效果 |
| `/agent-glance:restore` | 將裝置還原為原本的時鐘與相片狀態 |

## 運作原理

此韌體**沒有文字 API**,因此根本沒有可以「輸出」的對象。腳本改為用 Pillow 渲染一張 240×240 的 GIF,推送到裝置的 Photo 相簿中,並將該圖片設為唯一啟用的相片、Photo 設為唯一啟用的主題 —— 讓畫面固定不變,不會被輪替掉。

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

## 限制

- **7 個裝置主題無法各自顯示一個工作階段。** 只有 Photo 主題能呈現自訂內容,其餘六個都是固定的時鐘/天氣介面。要輪流顯示多個工作階段,就需要在相簿中放多張圖片 —— 目前尚未實作。
- 指標資料取自 Claude Code 的工作階段紀錄格式。在 Codex/agy 下狀態顏色仍可運作,但模型/token 欄位可能是空的。
- 狀態(`config.json`、`device_backup.json`)儲存在 `~/.agent-glance/` 而非外掛目錄下,外掛更新時也不會被清除。

## 授權

[MIT](../../../LICENSE)
