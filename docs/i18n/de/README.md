<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | **[Deutsch](README.md)** | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

# Agent Glance

> Verwandelt ein **GeekMagic SmallTV** in eine Live-Statusanzeige für deinen Agenten — für Claude Code, Codex und agy.

Der kleine Bildschirm zeigt, was dein Agent gerade tut: **WORKING**, **APPROVAL NEEDED** oder **DONE** — dazu Modell, Auslastung des Kontextfensters und Token-Zahlen, live aus dem Sitzungstranskript ausgelesen.
Das Killer-Feature ist der rote **APPROVAL**-Bildschirm: Stelle den Agenten auf einen anderen Monitor, und du kannst weggehen, kurz hinüberschauen und in dem Moment wissen, dass er auf dich wartet — statt es zehn Minuten später zu entdecken.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (bernstein) + der Prompt |
| approval needed | ⛔ **APPROVAL** (rot) + worum es geht |
| turn finished | ✓ **DONE** (grün) |

Jedes Bild zeigt außerdem `model · context bar + % · in/out tokens`.

## Voraussetzungen

- Ein GeekMagic SmallTV mit **SD_RU / SD Pro** Community-Firmware (ESP8266). Schnelltest — dies muss JSON mit einem `files`-Array zurückgeben:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  Die offizielle GeekMagic-Firmware und das ESP32-basierte "PRO" bieten eine *andere* API und werden **nicht unterstützt**.
  
- Das Gerät muss im selben WLAN wie dieser Rechner sein.
- Python 3.8+ mit Pillow (`pip install Pillow`).

## Installation

Verteilt über den Marketplace [`epicsagas/plugins`](https://github.com/epicsagas/plugins); das Plugin selbst liegt unter [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

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

### Was jeder Host bekommt

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | vollständig End-to-End verifiziert |
| Codex | ✅ | ✅ | ✅ | Hook-Datei entspricht dem dokumentierten Schema; zur Laufzeit nicht verifiziert |
| agy | ✅ | — | ✅ | Hook-Format entspricht einem tatsächlich installierten agy-Plugin; zur Laufzeit nicht verifiziert |
| hermes | ✅ | — | ❌ | nur Skills — hermes registriert sich über `register(ctx)`, ohne angebundene Lifecycle-Hooks |

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

## Befehle

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Vollständige Einrichtung — Gerät finden, Firmware prüfen, IP speichern, sichern, Kontrolle übernehmen |
| `/agent-glance:status` | Gesundheitscheck — Erreichbarkeit, aktives Theme, doppelte Hooks, Fehlerprotokoll |
| `/agent-glance:test` | Sendet ein Bild (oder alle drei nacheinander), um das Rendering zu prüfen |
| `/agent-glance:restore` | Setzt das Gerät auf seine ursprüngliche Uhr und Fotos zurück |

## Funktionsweise

Diese Firmware hat **keine Text-API**, es gibt also nichts, das man "ausgeben" könnte. Stattdessen rendert das Skript ein 240×240-GIF mit Pillow und lädt es in das Fotoalbum des Geräts hoch, wobei dieses Bild das einzig aktivierte Foto und Photo das einzig aktivierte Theme wird — so bleibt das Bild fest stehen, statt weiterzurotieren.

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

## Einschränkungen

- **Die 7 Gerätethemes können nicht jeweils eine eigene Sitzung anzeigen.** Nur das Photo-Theme rendert eigene Inhalte; die übrigen sechs sind feste Uhr-/Wetter-UIs. Mehrere Sitzungen zu rotieren würde mehrere Bilder im Album bedeuten — das ist nicht implementiert.
- Metriken stammen aus dem Transkriptformat von Claude Code. Unter Codex/agy funktionieren die Statusfarben weiterhin, aber die Modell-/Token-Felder können leer bleiben.
- Der Status (`config.json`, `device_backup.json`) liegt in `~/.agent-glance/`, nicht im Plugin-Verzeichnis, und wird daher bei Plugin-Updates nicht gelöscht.

## Lizenz

[MIT](../../../LICENSE)
