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

- **SD_RU / SD Pro** コミュニティファームウェア(ESP8266)搭載の GeekMagic SmallTV。簡単な確認方法 — 次のコマンドが `files` 配列を含む JSON を返す必要があります:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  GeekMagic 純正ファームウェアと ESP32 版「PRO」は *異なる* API を使用し、**非対応** です。
  
- デバイスはこのマシンと同じ Wi-Fi に接続している必要があります。
- Pillow をインストールした Python 3.8+ (`pip install Pillow`)。

## インストール

[`epicsagas/plugins`](https://github.com/epicsagas/plugins) マーケットプレイス経由で配布され、プラグイン本体は [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance) にあります。

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
| `AGENT_GLANCE_PRESET` | 表示プリセット: `default` \| `hosts` \| `anime` \| `custom` | `default` |
| `AGENT_GLANCE_LAYOUT` | gif モードのレイアウト: `frame` \| `fullscreen` | `frame` |

### GIF モードとプリセット

デフォルトモードは上で説明した静的なステータスフレームです。別のプリセットを選ぶと **gif モード** に切り替わり、中央にキャラクターを配置し、ヘッダーとステータスフッターを維持したままループするアニメーション GIF を合成します — この GIF はデバイス上でローカル再生されるため、状態ごとのアップロードは1回だけでフレームごとのネットワークトラフィックは発生しません。状態は上部のアクセントバーと背景色で引き続き表現されます。

| プリセット | 表示内容 |
|---|---|
| `default` | 静的フレーム(従来の挙動) |
| `hosts` | 同梱のホスト別キャラクター GIF を中央に表示、ヘッダーとフッターは維持 |
| `anime` | *予約済み* — スロットのみ存在、アートは未定。hosts のキャラクターにフォールバック |
| `custom` | ユーザー独自の GIF、ホスト別/状態別マッピング(スキーマ参照) |

プリセットは `--preset` CLI フラグで選択します(`--ip` と同じく `config.json` に保存されます):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` は `assets/hosts/` に中立的なプレースホルダを同梱しています。`<host>.gif` を `~/.agent-glance/gifs/hosts/` に置くことで上書きできます(例: `claude-code.gif`, `codex.gif`, `antigravity.gif`, `hermes.gif`, `agent.gif`) — ユーザーファイルが同梱ファイルより優先されます。

`custom` は `config.json` の `display.gifs` を読みます。各ホストのエントリは、パス文字列(全状態で1つの GIF)または状態別マップのいずれかで、`"default"` はフォールバックです。また、どのエントリも `{"path": ..., "layout": "fullscreen"}` の形で、そのエントリだけをフルスクリーンにすることもできます:

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
| `/agent-glance:restore` | デバイスを元の時計・写真の状態に戻す |

一部のオプションは **CLI フラグ専用** です(スラッシュコマンドはありません)。`--ip` と同様に `~/.agent-glance/config.json` に保存されます:

| フラグ | 動作 |
|---|---|
| `--ip <IP>` | デバイス IP を保存 |
| `--preset default\|hosts\|anime\|custom` | 表示モードを切り替え([GIF モード](#gif-モードとプリセット)参照) |
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

## 制限事項

- **7つのデバイステーマがそれぞれセッションを表示することはできません。** カスタムコンテンツを描画できるのは Photo テーマだけで、残り6つは固定の時計/天気 UI です。複数セッションをローテーション表示するにはアルバム内に複数の画像が必要ですが、未実装です。
- 指標は Claude Code のトランスクリプト形式から取得します。Codex/agy でも状態の色は機能しますが、モデル/トークンのフィールドは空欄になることがあります。
- 状態(`config.json`、`device_backup.json`)はプラグインディレクトリではなく `~/.agent-glance/` に保存され、プラグイン更新時にも消去されません。

## ライセンス

[MIT](../../../LICENSE)
