<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | **[Deutsch](README.md)** | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> Verwandelt ein **GeekMagic SmallTV** in eine Live-Statusanzeige für deinen Agenten — für Claude Code, Codex und agy.

Der kleine Bildschirm zeigt, was dein Agent gerade tut: **WORKING**, **APPROVAL NEEDED** oder **DONE** — dazu Modell, Auslastung des Kontextfensters und Token-Zahlen, live aus dem Sitzungstranskript ausgelesen.
Das Killer-Feature ist der rote **APPROVAL**-Bildschirm: Stelle den Agenten auf einen anderen Monitor, und du kannst weggehen, kurz hinüberschauen und in dem Moment wissen, dass er auf dich wartet — statt es zehn Minuten später zu entdecken.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (bernstein) + der Prompt |
| approval needed | ⛔ **APPROVAL** (rot) + worum es geht |
| turn finished | ✓ **DONE** (grün) |

Jedes Bild zeigt außerdem `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## Für wen ist das?

- **Du führst lange Agenten-Sitzungen aus** — Migrationen, Test-Suites, große Refactorings — und schaust ständig aufs Terminal, ob es fertig ist oder hängt.
- **Du gehst vom Keyboard weg** — und willst den *Moment* wissen, in dem der Agent deine Zustimmung braucht, nicht erst zehn Minuten später.
- **Du nutzt Claude Code / Codex / agy / hermes** headless und vermisst das visuelle Feedback einer vollwertigen IDE.
- **Du hast eine GeekMagic SmallTV**, die ungenutzt herumsteht, und willst, dass sie endlich ihren Teil beiträgt.

Wenn du schon mal zum Terminal zurückgekehrt bist und dachtest *"warte, hat die ganze Zeit auf mich gewartet?"* — dann ist das für dich.

## Voraussetzungen

- Ein GeekMagic SmallTV mit einer der unterstützten Firmwares (beim `--ip`-Speichern automatisch erkannt und gespeichert):
  - **SD_RU / SD Pro** Community-Firmware (ESP8266) — Schnellcheck — dieser Befehl muss JSON mit einem `files`-Array zurückgeben:

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra Stock-Firmware** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — Schnellcheck — dieser Befehl muss JSON mit einem `theme`-Schlüssel zurückgeben:

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  Andere GeekMagic-Stock-Firmware-Varianten und das ESP32 "PRO" verwenden eine *andere* API und werden **nicht** unterstützt.

- Das Gerät muss im selben WLAN wie dieser Rechner sein.
- Python 3.8+ mit Pillow (`pip install Pillow`).

## Installation

Eigenständige Installation aus diesem Repository — bringt den gleichnamigen `agent-glance`-Marktplatz mit; kein Hub nötig.

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

### Was jeder Host bekommt

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | vollständig End-to-End verifiziert |
| Codex | ✅ | ✅ | ✅ | Hook-Datei entspricht dem dokumentierten Schema; zur Laufzeit nicht verifiziert |
| agy | ✅ | — | ✅ | Hook-Format entspricht einem tatsächlich installierten agy-Plugin; zur Laufzeit nicht verifiziert |
| hermes | ✅ | — | ❌ | nur Skills — hermes registriert sich über `register(ctx)`, ohne angebundene Lifecycle-Hooks |
| Grok Build | ✅ | ✅ | ✅ | Hook-Datei folgt dem Claude-kompatiblen Schema; nicht zur Laufzeit verifiziert |

Danach das Gerät einrichten — das findet es, speichert die IP, sichert das Gerät und schaltet es in den Monitor-Modus:

```
/agent-glance:setup
```

Auf Hosts ohne Slash-Commands führst du dieselben Schritte manuell aus:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Die Hooks werden mit dem Plugin ausgeliefert und aktivieren sich von selbst. **Starte den Agenten nach der Installation neu** — Hooks werden beim Sitzungsstart geladen.

## Konfiguration

Die Konfiguration wird **zuerst über Umgebungsvariablen** gelesen und fällt sonst auf `~/.agent-glance/config.json` zurück (geschrieben von `--ip`). Die Umgebungsvariable ist die portablere Option für gemeinsam genutzte oder Mehrrechner-Setups.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | Geräte-IP — **erforderlich** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | Kontextfenster zur Skalierung der %-Anzeige | `200000` |
| `AGENT_GLANCE_PRESET` | Anzeigepreset: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | GIF-Modus-Layout: `frame` \| `fullscreen` | `frame` |

### GIF-Modus & Presets

> [!WARNING]
> **Warnung zur GIF-Dateigröße**: Zu große GIF-Dateien belasten den Speicher des Geräts (ESP8266 RAM/Flash) stark und können zu unerwarteten Neustarts oder Abstürzen führen. Bitte halte deine GIFs unbedingt unter **< 100 KB**.

Der Standardmodus ist das oben beschriebene statische Status-Frame. Wähle ein anderes Preset, um in den **GIF-Modus** zu wechseln, der eine endlos laufende animierte GIF zusammensetzt (Charakter in der Mitte, Header + Status-Footer bleiben erhalten) und vom Gerät lokal abgespielt wird — ein Upload pro Status, kein Netzwerkverkehr pro Frame. Der Status wird weiterhin über die Akzentleiste oben + die Hintergrundfarbe signalisiert.

| Preset | What it shows |
|---|---|
| `default` | Statisches Frame (ursprüngliches Verhalten) |
| `hosts` | Ein mitgeliefertes pro-Host-Charakter-GIF in der Mitte; Header + Footer bleiben erhalten |
| `custom` | Eigene GIFs, pro Host und/oder pro Status (siehe Schema) |

Wähle ein Preset mit dem CLI-Flag `--preset` (wird wie `--ip` in `config.json` gespeichert):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` wird mit neutralen Platzhaltern in `assets/gif/` ausgeliefert, sodass es sofort einsatzbereit ist. Um deinen eigenen Charakter zu verwenden, lege eine GIF im Benutzerverzeichnis ab — sie hat Vorrang vor der mitgelieferten, und der Bildschirm wird beim nächsten Status-Push aktualisiert (kein Neustart nötig):

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

Benenne die Datei nach dem Host, den sie ersetzen soll (Kleinschreibung, Leerzeichen → Bindestriche):

| Erkannter Host | Dateiname zum Überschreiben |
|---|---|
| Claude Code | `claude-code.gif` |
| Codex | `codex.gif` |
| Antigravity | `antigravity.gif` |
| Hermes | `hermes.gif` |
| jeder andere Host | `agent.gif` |

### Optimale GIF-Spezifikationen

| Parameter | `frame`-Layout | `fullscreen`-Layout |
|---|---|---|
| **Optimale Auflösung** | **224 × 116 px** (~1,93:1) oder **116 × 116 px** (1:1) | **240 × 240 px** (1:1 quadratisch) |
| **Zielbereich** | Passt in `MIDDLE_BOX = (8, 46, 224, 116)` | Deckt den gesamten 1,54" SmallTV-Bildschirm ab |
| **Empfohlene Dateigröße** | **< 100 KB** (Absolutes Maximum < 300 KB zur Vermeidung von ESP8266 RAM/OOM-Abstürzen & Neustarts) |
| **Frame-Anzahl** | **12 – 16 Frames** (Renderer reduziert über absolute Werte hinaus auf `_MAX_FRAMES = 16`) |
| **Frame-Verzögerung** | **80ms – 150ms** pro Frame (1,2s – 2,0s Schleife) |
| **Farbpalette** | **64 – 128 Farben** (optimiert Rendering-Geschwindigkeit und Flash-Verschleiß) |

**Ausgangs-GIF auf die Spezifikation verkleinern** (rohe Exporte landen leicht im mehrstelligen MB-Bereich): Frames gleichmäßig über den gesamten Clip verteilt entnehmen und dann mit einer kurzen Ziel-Schleife neu kodieren, damit der volle Bewegungsumfang erhalten bleibt, auch wenn die Wiedergabegeschwindigkeit komprimiert wird.

1 — ~14 Frames gleichmäßig über die Quelle verteilt entnehmen, je nach Layout zugeschnitten/skaliert:

```bash
# frame-Layout: wird in MIDDLE_BOX eingepasst, also nur verkleinern (kein Zuschnitt nötig)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen-Layout: wird auf 240x240 gestreckt, also erst quadratisch zuschneiden, sonst verzerrt es
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = Anzahl der Quell-Frames ÷ 14 (abgerundet) — per ffprobe ermitteln (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`).

2 — die entnommenen Frames mit einer kurzen Ziel-Schleife (10fps = 100ms/Frame ≈ 1,4s Schleife bei 14 Frames) und kleiner Palette neu kodieren:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Immer noch über 300 KB? Erst `max_colors` auf 32 senken (auch `dither=none` probieren), bevor die Frame-Anzahl reduziert wird — das ist der eigentliche Kostentreiber der Schleife.



`custom` liest `display.gifs` aus `config.json`. Jeder Host-Eintrag ist entweder ein Pfad-String (ein GIF für alle Status) oder eine pro-Status-Map; `"default"` ist der Fallback. Jeder Eintrag kann auch als `{"path": ..., "layout": "fullscreen"}` angegeben werden, um nur für diesen auf Full-Screen zu schalten:

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

Auflösungsreihenfolge pro Push: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → mitgelieferte hosts-Platzhalter. Eine fehlende oder unlesbare GIF leert den Bildschirm nie — sie fällt auf das statische Frame zurück.

## Befehle

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Vollständige Einrichtung — Gerät finden, Firmware prüfen, IP speichern, sichern, Kontrolle übernehmen |
| `/agent-glance:status` | Gesundheitscheck — Erreichbarkeit, aktives Theme, doppelte Hooks, Fehlerprotokoll |
| `/agent-glance:test` | Sendet ein Bild (oder alle drei nacheinander), um das Rendering zu prüfen |
| `/agent-glance:theme` | Kurz auf die Geräte-eigenen Bildschirme schauen — Wetter, Vorhersage, Uhren (Ultra; der Monitor kehrt bei der nächsten Aktivität zurück) |
| `/agent-glance:restore` | Setzt das Gerät auf seine ursprüngliche Uhr und Fotos zurück |

Einige Optionen gibt es **nur als CLI-Flag** (kein Slash-Command) — sie werden in `~/.agent-glance/config.json` gespeichert, analog zu `--ip`:

| Flag | What it does |
|---|---|
| `--ip <IP>` | Geräte-IP speichern |
| `--preset default\|hosts\|custom` | Anzeigemodus wechseln (siehe [GIF-Modus](#gif-modus--presets)) |
| `--layout frame\|fullscreen` | GIF-Modus-Layout (`frame` behält Header+Footer; `fullscreen` ist nur das GIF) |
| `--test [state] [subtitle]` | Ein Frame pushen; respektiert das aktuelle Preset, zeigt also auch eine Vorschau des GIF-Modus |

## Funktionsweise

Diese Firmware hat **keine Text-API**, es gibt also nichts, das man "ausgeben" könnte. Stattdessen rendert das Skript ein 240×240-GIF mit Pillow und lädt es in das Fotoalbum des Geräts hoch, wobei dieses Bild das einzig aktivierte Foto und Photo das einzig aktivierte Theme wird — so bleibt das Bild fest stehen, statt weiterzurotieren. Der GIF-Decoder der Firmware spielt außerdem **animierte** GIFs ab, sodass das Skript im GIF-Modus ein Multi-Frame-GIF zusammensetzt und das Gerät es lokal als Schleife abspielt — ein Upload pro Status, kein Netzwerkverkehr pro Frame.

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

## Multi-Host-Hooks

Die drei Hosts teilen sich **kein** gemeinsames Hook-Format, daher hat jeder seine eigene Datei. Es gibt absichtlich kein generisches `hooks/hooks.json` — dieser Pfad ist der Standard sowohl für Claude Code als auch für Codex, und würde man eine Datei dort belassen, würde der falsche Host sie laden.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | in `.claude-plugin/plugin.json` deklariert |
| Codex | `.codex-plugin/hooks.json` | in `.codex-plugin/plugin.json` deklariert |
| agy | `hooks.json` (Plugin-**Wurzel**) | erzwungen — das Manifest-Schema von agy ist `additionalProperties:false`, sodass der Pfad nicht deklariert werden kann |

Da die Hosts unterschiedliche Lifecycles bieten, unterscheiden sich auch die Events:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

Und die Payloads unterscheiden sich: Claude Code und Codex senden `hook_event_name` / `transcript_path` (snake_case); agy sendet `hookEventName` / `transcriptPath` (camelCase) und verpackt seine Konfiguration in einer benannten Hook-Gruppe. Das Skript normalisiert das alles.

Nur Claude Code ersetzt `${CLAUDE_PLUGIN_ROOT}` innerhalb von Hook-Befehlen, daher referenzieren die anderen beiden direkt ihren eigenen installierten Plugin-Pfad:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Geräte-API-Referenz (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Eigenheiten, die beim Untersuchen eines echten Geräts gefunden wurden:

- `state` muss `1` / `0` sein. Die Firmware führt `atoi()` darauf aus, sodass `"true"` zu `0` wird und stillschweigend das Gegenteil des Beabsichtigten tut.
- Das Deaktivieren des *letzten* aktivierten Themes oder Fotos liefert **HTTP 403** — ein Schutz gegen einen leeren Bildschirm. Das Setup aktiviert zuerst das Ziel und deaktiviert dann den Rest.
- Der ESP8266 ist single-threaded und liefert 403, wenn er mit einer vorherigen Anfrage beschäftigt ist, daher werden Uploads wiederholt.
- ⚠️ `/config` liefert das WLAN-Passwort des Geräts und den Wetter-API-Schlüssel **im Klartext und ohne Authentifizierung**. Das ist Verhalten der Firmware, nicht etwas, das dieses Plugin hinzufügt — behandle das Gerät in einem gemeinsam genutzten Netzwerk dennoch als nicht vertrauenswürdig.

## Geräte-API-Referenz (SmallTV Ultra Stock-Firmware)

Themes: 1 Wetteruhr Heute · 2 Wettervorhersage · **3 Fotoalbum** · 4–6 Uhrstile · 7 Einfache Wetteruhr.

| Action | Endpoint |
|---|---|
| Bild hochladen | `POST /doUpload?dir=/image/` (multipart-Feld `image`; erneutes Hochladen unter gleichem Namen überschreibt) |
| auf dem Bildschirm anheften | `GET /set?img=/image/<f>` (URL-kodiert; erfordert Theme 3) |
| Theme wechseln | `GET /set?theme=<n>` |
| Theme-Flags | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| Datei löschen | `GET /delete?file=/image/<f>` |
| Status lesen | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

Beim Sondieren eines echten Geräts gefundene Stolpersteine:

- Das angezeigte Bild wird per `/set?img=` *angepinnt* — die übrigen Albumdateien bleiben, rotieren aber nie ein (keine Foto-Enable-Flags wie bei SD_RU; setup fasst sie nicht an).
- Animierte GIFs werden lokal dekodiert und geloopt; das ganze 3-MB-Dateisystem wird mit Wetter-/Uhr-Assets geteilt — GIFs also klein halten (~1 MB frei ab Werk).
- `/set?img=` und `/set?theme=` antworten mit dem Literal `OK`, nicht mit JSON.
- ⚠️ gleiches Vertrauensmodell wie SD_RU: jeder Endpunkt ist im LAN ohne Authentifizierung offen.

## Einschränkungen

- **Die 7 Gerätethemes können nicht jeweils eine eigene Sitzung anzeigen.** Nur das Photo-Theme rendert eigene Inhalte; die übrigen sechs sind feste Uhr-/Wetter-UIs. Mehrere Sitzungen zu rotieren würde mehrere Bilder im Album bedeuten — das ist nicht implementiert.
- Metriken stammen aus dem Transkriptformat von Claude Code. Unter Codex/agy funktionieren die Statusfarben weiterhin, aber die Modell-/Token-Felder können leer bleiben.
- Der Status (`config.json`, `device_backup.json`) liegt in `~/.agent-glance/`, nicht im Plugin-Verzeichnis, und wird daher bei Plugin-Updates nicht gelöscht.

## Lizenz

[MIT](../../../LICENSE)
