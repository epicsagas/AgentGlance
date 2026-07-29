<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | **[Italiano](README.md)**

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> Trasforma una **GeekMagic SmallTV** in un display di stato live per il tuo agente — per Claude Code, Codex e agy.

Il piccolo schermo mostra cosa sta facendo il tuo agente in questo momento: **WORKING**, **APPROVAL NEEDED** o **DONE** — oltre a modello, utilizzo della finestra di contesto e conteggio dei token, presi in tempo reale dalla trascrizione della sessione.
La funzionalità di punta è la schermata rossa di **APPROVAL**: metti l'agente su un altro monitor e potrai allontanarti, darci un'occhiata e sapere nell'istante in cui è bloccato in attesa della tua approvazione, invece di scoprirlo dieci minuti dopo.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (ambra) + il prompt |
| approval needed | ⛔ **APPROVAL** (rosso) + ciò che richiede |
| turn finished | ✓ **DONE** (verde) |

Ogni fotogramma riporta anche `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## Requisiti

- Una GeekMagic SmallTV con firmware community **SD_RU / SD Pro** (ESP8266). Verifica rapida — questo deve restituire JSON con un array `files`:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  Il firmware ufficiale GeekMagic e il "PRO" basato su ESP32 espongono un'API *diversa* e **non sono supportati**.
  
- Il dispositivo deve trovarsi sulla stessa rete Wi-Fi di questa macchina.
- Python 3.8+ con Pillow (`pip install Pillow`).

## Installazione

Distribuito tramite il marketplace [`epicsagas/plugins`](https://github.com/epicsagas/plugins); il plugin vero e proprio si trova in [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

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

### Cosa ottiene ciascun host

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | verificato end-to-end |
| Codex | ✅ | ✅ | ✅ | il file degli hook corrisponde allo schema documentato; non verificato a runtime |
| agy | ✅ | — | ✅ | il formato degli hook corrisponde a un plugin agy realmente installato; non verificato a runtime |
| hermes | ✅ | — | ❌ | solo skill — hermes si registra tramite `register(ctx)`, senza hook di ciclo di vita collegati |

Poi effettua l'onboarding del dispositivo — questo lo trova, salva l'IP, ne fa un backup e lo passa alla modalità monitor:

```
/agent-glance:setup
```

Sugli host senza comandi slash, esegui gli stessi passaggi a mano:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Gli hook sono inclusi nel plugin e si attivano da soli. **Riavvia l'agente dopo l'installazione** — gli hook vengono caricati all'avvio della sessione.

## Configurazione

La configurazione viene letta **prima dalle variabili d'ambiente**, e in loro assenza ricade su `~/.agent-glance/config.json` (scritto da `--ip`). La variabile d'ambiente è l'opzione più portabile per configurazioni condivise o multi-macchina.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | IP del dispositivo — **obbligatorio** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | finestra di contesto usata per scalare la barra percentuale | `200000` |

## Comandi

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Onboarding completo — individua il dispositivo, verifica il firmware, salva l'IP, esegue il backup, prende il controllo |
| `/agent-glance:status` | Controllo di stato — raggiungibilità, tema attivo, hook duplicati, log degli errori |
| `/agent-glance:test` | Invia un fotogramma (o li fa scorrere tutti e tre) per verificare il rendering |
| `/agent-glance:restore` | Riporta il dispositivo al suo orologio e alle foto originali |

## Come funziona

Questo firmware **non ha un'API testuale**, quindi non c'è nulla da "stampare". Lo script renderizza invece una GIF 240×240 con Pillow e la carica nell'album foto del dispositivo, rendendo quell'immagine l'unica foto abilitata e Photo l'unico tema abilitato — così il fotogramma resta fisso invece di ruotare via.

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

## Hook multi-host

I tre host **non** condividono lo stesso formato di hook, quindi ciascuno ha il proprio file. Non esiste deliberatamente un `hooks/hooks.json` generico — quel percorso è quello predefinito sia per Claude Code sia per Codex, e lasciarne uno lì farebbe sì che l'host sbagliato lo carichi.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | dichiarato in `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | dichiarato in `.codex-plugin/plugin.json` |
| agy | `hooks.json` (**radice** del plugin) | forzato — lo schema del manifest di agy è `additionalProperties:false`, quindi il percorso non può essere dichiarato |

Poiché gli host espongono cicli di vita diversi, anche gli eventi differiscono:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

E i payload differiscono: Claude Code e Codex inviano `hook_event_name` / `transcript_path` (snake_case); agy invia `hookEventName` / `transcriptPath` (camelCase) e avvolge la propria configurazione in un gruppo di hook con nome. Lo script normalizza tutto questo.

Solo Claude Code sostituisce `${CLAUDE_PLUGIN_ROOT}` all'interno dei comandi degli hook, quindi gli altri due fanno riferimento direttamente al percorso del proprio plugin installato:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Riferimento API del dispositivo (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Stranezze scoperte esaminando un dispositivo reale:

- `state` deve essere `1` / `0`. Il firmware ci esegue sopra `atoi()`, quindi `"true"` diventa `0` e fa silenziosamente il contrario di quanto previsto.
- Disabilitare l'*ultimo* tema o foto abilitati restituisce **HTTP 403** — una protezione contro lo schermo vuoto. Il setup abilita prima l'obiettivo e poi disabilita il resto.
- L'ESP8266 è single-threaded e restituisce 403 quando è occupato con una richiesta precedente, quindi i caricamenti vengono ritentati.
- ⚠️ `/config` espone la password Wi-Fi del dispositivo e la chiave dell'API meteo **in chiaro e senza alcuna autenticazione**. È un comportamento del firmware, non qualcosa che aggiunge questo plugin — ma tratta comunque il dispositivo come non affidabile su una rete condivisa.

## Limitazioni

- **I 7 temi del dispositivo non possono mostrare ciascuno una sessione.** Solo il tema Photo renderizza contenuti personalizzati; gli altri sei sono interfacce fisse di orologio/meteo. Far ruotare più sessioni richiederebbe più immagini nell'album — non è implementato.
- Le metriche provengono dal formato di trascrizione di Claude Code. Su Codex/agy i colori di stato funzionano comunque, ma i campi modello/token possono restare vuoti.
- Lo stato (`config.json`, `device_backup.json`) risiede in `~/.agent-glance/`, non nella directory del plugin, quindi non viene cancellato negli aggiornamenti del plugin.

## Licenza

[MIT](../../../LICENSE)
