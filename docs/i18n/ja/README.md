<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | **[日本語](README.md)** | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> **GeekMagic SmallTV** をリアルタイムのエージェントステータス表示器に変えます — Claude Code、Codex、agy 向け。

小さなTV画面に、いまエージェントが何をしているかを表示します:**WORKING**、**APPROVAL NEEDED**、**DONE** — さらにライブのセッショントランスクリプトから取得したモデル名、コンテキストウィンドウ使用率、トークン数も一緒に表示します。
一番の目玉は赤い **APPROVAL** 画面です。エージェントを別のモニターに表示しておけば、席を離れていても、ちらっと見るだけで承認待ちになった瞬間にわかります。10分後に気づく、ということがなくなります。

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING**(アンバー)+ プロンプト |
| approval needed | ⛔ **APPROVAL**(レッド)+ 求めている内容 |
| turn finished | ✓ **DONE**(グリーン) |

各フレームには `model · context bar + % · in/out tokens` も表示されます。

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## こんな人にぴったり

- **長時間のエージェントセッションを走らせる人** — マイグレーション、テストスイート、大規模リファクタなど — 終わったか止まったか気になって何度もターミナルを確認してしまうなら。
- **席を離れる人** — エージェントが承認待ちになった *瞬間* を、10分後ではなく今すぐ知りたいなら。
- **Claude Code / Codex / agy / hermes をヘッドレスで使い**、フルIDEがくれる視覚的フィードバックが恋しい人。
- **GeekMagic SmallTV を持っているのに** ほったらかしで、きちんと働いてほしい人。

ターミナルに戻って *「待って、ずっと私の承認を待ってたの？」* と思ったことがあるなら — これはあなたのためのものです。

## 必要条件

- 対応するファームウェアのいずれかが動作する GeekMagic SmallTV（`--ip` 保存時に自動検出・記録）:
  - **SD_RU / SD Pro** コミュニティファームウェア (ESP8266) — 簡単チェック — このコマンドは `files` 配列を含む JSON を返す必要があります:

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra 標準ファームウェア** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — 簡単チェック — このコマンドは `theme` キーを含む JSON を返す必要があります:

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  その他の GeekMagic 標準ファームウェアおよび ESP32 "PRO" は*異なる* API を使用し、**サポートされません**。

- デバイスはこのマシンと同じ Wi-Fi に接続している必要があります。
- Pillow をインストールした Python 3.8+ (`pip install Pillow`)。

## インストール

このリポジトリから単体でインストール — プラグインと同名の `agent-glance` マーケットプレイスを同梱、ハブは不要です。

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

### 各ホストでできること

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | エンドツーエンドで検証済み |
| Codex | ✅ | ✅ | ✅ | フックファイルは文書化されたスキーマと一致;ランタイム未検証 |
| agy | ✅ | — | ✅ | 実際にインストールされた agy プラグインとフック形式が一致;ランタイム未検証 |
| hermes | ✅ | — | ❌ | スキルのみ対応 — hermes は `register(ctx)` で登録するだけで、ライフサイクルフックは接続されていません |

続いてデバイスをオンボーディングします — デバイスを検出し、IP を保存し、デバイスをバックアップしてからモニターモードに切り替えます:

```
/agent-glance:setup
```

スラッシュコマンドがないホストでは、同じ手順を手動で実行します:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

フックはプラグインに同梱されており、自動的に有効化されます。**インストール後はエージェントを再起動してください** — フックはセッション開始時に読み込まれます。

## 設定

設定は **環境変数を優先** して読み込み、なければ `~/.agent-glance/config.json`(`--ip` で書き込まれる)にフォールバックします。共有環境や複数マシン構成では環境変数の方が可搬性が高い選択肢です。

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | デバイス IP — **必須** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | パーセントバーのスケールに使うコンテキストウィンドウサイズ | `200000` |
| `AGENT_GLANCE_PRESET` | 表示プリセット: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | gif モードのレイアウト: `frame` \| `fullscreen` | `frame` |

### GIF モードとプリセット

> [!WARNING]
> **GIF ファイルサイズに関する注意**: 容量の大きい GIF ファイルはデバイスのメモリ(ESP8266 RAM/Flash)に大きな負荷をかけ、予期せぬ再起動やクラッシュの原因となります。ファイルサイズは必ず **< 100 KB** に抑えてください。

デフォルトモードは上で説明した静的なステータスフレームです。別のプリセットを選ぶと **gif モード** に切り替わり、中央にキャラクターを配置し、ヘッダーとステータスフッターを維持したままループするアニメーション GIF を合成します — この GIF はデバイス上でローカル再生されるため、状態ごとのアップロードは1回だけでフレームごとのネットワークトラフィックは発生しません。状態は上部のアクセントバーと背景色で引き続き表現されます。

| プリセット | 表示内容 |
|---|---|
| `default` | 静的フレーム(従来の挙動) |
| `hosts` | 同梱のホスト別キャラクター GIF を中央に表示、ヘッダーとフッターは維持 |
| `custom` | ユーザー独自の GIF、ホスト別/状態別マッピング(スキーマ参照) |

プリセットは `--preset` CLI フラグで選択します(`--ip` と同じく `config.json` に保存されます):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` は `assets/gif/` に中立的なプレースホルダを同梱しています。`<host>.gif` を `~/.agent-glance/gifs/hosts/` に置くことで上書きできます(例: `claude-code.gif`, `codex.gif`, `antigravity.gif`, `hermes.gif`, `agent.gif`) — ユーザーファイルが同梱ファイルより優先されます。

### GIF 最適規格および推奨仕様

| 項目 | `frame` レイアウト | `fullscreen` レイアウト |
|---|---|---|
| **最適解像度** | **224 × 116 px** (アスペクト比約 1.93:1) または **116 × 116 px** (1:1) | **240 × 240 px** (1:1 正方形) |
| **合成対象** | `MIDDLE_BOX = (8, 46, 224, 116)` 内に自動調整 | SmallTV 1.54インチ全画面を非表示カバー |
| **推奨ファイルサイズ** | **< 100 KB** (ESP8266 の RAM/OOM クラッシュおよび再起動防止のため最大 < 300 KB) |
| **フレーム数** | **12 – 16 フレーム** (レンダラーにより `_MAX_FRAMES = 16` に自動ダウンサンプル) |
| **フレームディレイ** | **80ms – 150ms** / フレーム (1.2秒 – 2.0秒ループ) |
| **カラーパレット** | **64 – 128 色** (レンダリング速度最適化および Flash メモリ保護) |

**元 GIF を規格まで縮小する**(未加工のエクスポートは簡単に数 MB を超えます): クリップ全体から均等にフレームをサンプリングし、短いターゲットループで再エンコードすることで、再生速度を圧縮しても動きの幅全体を保持します。

1 — レイアウトに応じてクロップ/スケーリングしつつ、元動画から約14フレームを均等にサンプリング:

```bash
# frame レイアウト: MIDDLE_BOX にレターボックスで収まるので、縮小するだけでよい(クロップ不要)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen レイアウト: 240x240 に引き伸ばされるので、先に正方形にクロップしないと歪む
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = 元動画のフレーム数 ÷ 14(切り捨て)— ffprobe で取得(`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`)。

2 — サンプリングしたフレームを短いターゲットループ(10fps = 100ms/フレーム ≈ 14フレームで約1.4秒ループ)と小さいパレットで再エンコード:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

それでも300 KBを超える場合は、フレーム数を減らす前に `max_colors` を32に下げる(`dither=none` も試す)— ループのコストを実際に左右するのはそこ。


`custom` は `config.json` の `display.gifs` を読みます。各ホストのエントリは、パス文字列(全状態で1つの GIF)または状態別マップのいうずれかで、`"default"` はフォールバックです。また、どのエントリも `{"path": ..., "layout": "fullscreen"}` の形で、そのエントリだけをフルスクリーンにすることもできます:

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

プッシュごとの解決順序: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → 同梱の hosts プレースホルダ。存在しない、あるいは読み込めない GIF が画面を空白にすることはありません — 静的フレームにフォールバックします。

## コマンド

| Command | What it does |
|---|---|
| `/agent-glance:setup` | フルオンボーディング — デバイス検出、ファームウェア確認、IP 保存、バックアップ、制御権取得 |
| `/agent-glance:status` | ヘルスチェック — 疎通確認、有効なテーマ、重複フック、エラーログ |
| `/agent-glance:test` | フレームを1つ(または3種類すべて)送信して表示を確認 |
| `/agent-glance:theme` | 端末本体の画面を一時表示 — 天気・予報・時計（Ultra 専用。モニターは次のアクティビティで自動復帰） |
| `/agent-glance:restore` | デバイスを元の時計・写真の状態に戻す |

一部のオプションは **CLI フラグ専用** です(スラッシュコマンドはありません)。`--ip` と同様に `~/.agent-glance/config.json` に保存されます:

| フラグ | 動作 |
|---|---|
| `--ip <IP>` | デバイス IP を保存 |
| `--preset default\|hosts\|custom` | 表示モードを切り替え([GIF モード](#gif-モードとプリセット)参照) |
| `--layout frame\|fullscreen` | gif モードのレイアウト(`frame` はヘッダー+フッターを維持、`fullscreen` は GIF のみ) |
| `--test [state] [subtitle]` | フレームをプッシュ、現在のプリセットに従うため gif モードのプレビューにも使えます |

## 仕組み

このファームウェアには **テキスト API がなく**、そもそも「表示」できる対象がありません。代わりにスクリプトが Pillow で 240×240 の GIF を描画してデバイスの Photo アルバムに入れ、その画像だけを有効な写真に、Photo だけを有効なテーマにします — こうすることで画面が他のテーマに切り替わらず固定されます。このファームウェアの GIF デコーダは **アニメーション** GIF も再生するため、gif モードではマルチフレーム GIF を合成し、デバイスがそれをローカルでループ再生します — 状態ごとのアップロードは1回、フレームごとのトラフィックは発生しません。

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

## マルチホストフック

3つのホストはフック形式を共有して **いない** ため、それぞれ専用のファイルを持ちます。汎用の `hooks/hooks.json` があえて存在しないのは、そのパスが Claude Code と Codex *両方* のデフォルトであり、そのまま置いてしまうと意図しないホストに読み込まれてしまうからです。

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | `.claude-plugin/plugin.json` で宣言 |
| Codex | `.codex-plugin/hooks.json` | `.codex-plugin/plugin.json` で宣言 |
| agy | `hooks.json`(プラグイン **ルート**) | 強制 — agy のマニフェストスキーマが `additionalProperties:false` のため、パスを個別に宣言できない |

ホストごとにライフサイクルが異なるため、イベントも異なります:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

ペイロードも異なります: Claude Code と Codex は `hook_event_name` / `transcript_path`(スネークケース)を送り、agy は `hookEventName` / `transcriptPath`(キャメルケース)を送って、設定を名前付きフックグループでラップします。スクリプトがこれらすべてを正規化します。

フックコマンド内で `${CLAUDE_PLUGIN_ROOT}` を置換するのは Claude Code だけなので、残る2つは自身のインストール済みプラグインパスを直接参照します:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## デバイス API リファレンス (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

実機を調べて見つかった注意点:

- `state` は必ず `1` / `0` でなければなりません。ファームウェアが `atoi()` を実行するため、`"true"` は `0` になり、意図とは逆の動作を静かに行います。
- 最後に残った有効なテーマや写真を無効化すると **HTTP 403** が返ります — 画面が空白になるのを防ぐガードです。セットアップは対象を先に有効化してから残りを無効化します。
- ESP8266 はシングルスレッドで、前のリクエスト処理中は 403 を返すため、アップロードはリトライします。
- ⚠️ `/config` は認証なしでデバイスの **Wi-Fi パスワードと天気 API キーを平文で** 提供します。これはこのプラグインが追加したものではなくファームウェア自体の挙動です — ただし共有ネットワーク上ではこのデバイスを信頼できないものとして扱ってください。

## デバイス API リファレンス（SmallTV Ultra 標準ファームウェア）

テーマ: 1 今日の天気時計 · 2 天気予報 · **3 フォトアルバム** · 4–6 時計スタイル · 7 シンプル天気時計。

| Action | Endpoint |
|---|---|
| 画像アップロード | `POST /doUpload?dir=/image/` (multipart フィールド `image`; 同名再アップロードは上書き) |
| 画面にピン留め | `GET /set?img=/image/<f>` (URL エンコード必須; テーマ 3 が必要) |
| テーマ切替 | `GET /set?theme=<n>` |
| テーマフラグ | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| ファイル削除 | `GET /delete?file=/image/<f>` |
| 状態読み取り | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

実機プロービングで判明した注意点:

- 表示画像は `/set?img=` で*ピン留め*されます — アルバムの他ファイルは残りますがローテーションしません（SD_RU のような写真ごとの有効フラグはなく、setup は触れません）。
- アニメーション GIF は端末内でデコード・ループ再生されます。3MB のファイルシステム全体を天気/時計アセットと共有するため、GIF は小さく保ってください（工場状態で約 1MB 空き）。
- `/set?img=` と `/set?theme=` は JSON ではなくリテラルテキスト `OK` を返します。
- ⚠️ SD_RU と同じ信頼モデル: すべてのエンドポイントが LAN 上で認証なしです。

## 制限事項

- **7つのデバイステーマがそれぞれセッションを表示することはできません。** カスタムコンテンツを描画できるのは Photo テーマだけで、残り6つは固定の時計/天気 UI です。複数セッションをローテーション表示するにはアルバム内に複数の画像が必要ですが、未実装です。
- 指標は Claude Code のトランスクリプト形式から取得します。Codex/agy でも状態の色は機能しますが、モデル/トークンのフィールドは空欄になることがあります。
- 状態(`config.json`、`device_backup.json`)はプラグインディレクトリではなく `~/.agent-glance/` に保存され、プラグイン更新時にも消去されません。

## ライセンス

[MIT](../../../LICENSE)
