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

## Per chi è?

- **Lanci sessioni lunghe dell'agente** — migrazioni, suite di test, grandi refactor — e continui a controllare il terminale per capire se ha finito o se è bloccato.
- **Ti allontani dalla tastiera** — e vuoi sapere l' *istante* in cui l'agente ha bisogno della tua approvazione, non dieci minuti dopo.
- **Usi Claude Code / Codex / agy / hermes** in modalità headless e ti manca il feedback visivo che darebbe un IDE completo.
- **Hai una GeekMagic SmallTV** inutilizzata e vuoi che si guadagni da vivere.

Se sei mai tornato al terminale pensando *"aspetta, era tutto questo tempo che mi aspettava?"* — allora è per te.

## Requisiti

- Un GeekMagic SmallTV con uno dei firmware supportati (rilevato automaticamente e salvato con `--ip`):
  - **SD_RU / SD Pro** firmware della community (ESP8266) — verifica rapida — questo comando deve restituire JSON con un array `files`:

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra firmware stock** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — verifica rapida — questo comando deve restituire JSON con una chiave `theme`:

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  Le altre varianti del firmware stock GeekMagic e la "PRO" ESP32 espongono un'API *diversa* e **non** sono supportate.

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
| `AGENT_GLANCE_PRESET` | preset di visualizzazione: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | layout modalità gif: `frame` \| `fullscreen` | `frame` |

### Modalità GIF e preset

> [!WARNING]
> **Avviso sulla dimensione GIF**: I file GIF di grandi dimensioni mettono a dura prova la memoria del dispositivo (RAM/Flash dell'ESP8266) e possono causare riavvii o crash inaspettati. Si raccomanda di mantenere i file sotto **< 100 KB**.

La modalità predefinita è il fotogramma di stato statico descritto sopra. Scegli un altro preset per passare alla **modalità gif**, che compone una GIF animata in loop (personaggio al centro, con header + footer di stato mantenuti) riprodotta localmente dal dispositivo — un caricamento per stato, nessun traffico di rete per ogni fotogramma. Lo stato è comunque segnalato dalla barra colorata superiore + dal colore di sfondo.

| Preset | Cosa mostra |
|---|---|
| `default` | Fotogramma statico (il comportamento originale) |
| `hosts` | Una GIF carattere per host in bundle al centro; header + footer mantenuti |
| `custom` | Le tue GIF, per host e/o per stato (vedi schema) |

Scegli un preset con il flag CLI `--preset` (viene salvato in `config.json`, come `--ip`):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` viene fornito con segnaposto neutri in `assets/gif/`, così funziona fin da subito. Per usare un tuo personaggio, inserisci una GIF nella directory utente — ha la precedenza su quella in bundle, e lo schermo si aggiorna al prossimo push di stato (nessun riavvio):

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

Dai al file il nome dell'host che deve sostituire (minuscolo, spazi → trattini):

| Host rilevato | File di override |
|---|---|
| Claude Code | `claude-code.gif` |
| Codex | `codex.gif` |
| Antigravity | `antigravity.gif` |
| Hermes | `hermes.gif` |
| qualsiasi altro host | `agent.gif` |

### Specifiche GIF ottimali

| Parametro | Layout `frame` | Layout `fullscreen` |
|---|---|---|
| **Risoluzione ottimale** | **224 × 116 px** (~1.93:1) o **116 × 116 px** (1:1) | **240 × 240 px** (1:1 quadrato) |
| **Obiettivo di composizione** | Si adatta a `MIDDLE_BOX = (8, 46, 224, 116)` | Copre l'intero schermo SmallTV da 1.54" |
| **Dimensione file consigliata** | **< 100 KB** (Massimo rigoroso < 300 KB per evitare crash RAM/OOM e riavvii dell'ESP8266) |
| **Numero di fotogrammi** | **12 – 16 fotogrammi** (il renderer riduce i fotogrammi in eccesso a `_MAX_FRAMES = 16`) |
| **Ritardo fotogramma** | **80ms – 150ms** per fotogramma (loop da 1.2s – 2.0s) |
| **Tavolozza colori** | **64 – 128 colori** (ottimizza la velocità di rendering e l'usura della Flash) |

**Ridurre una GIF sorgente alla specifica** (gli export grezzi superano facilmente diversi MB): campiona i fotogrammi in modo uniforme lungo l'intera clip, poi ricodifica con un loop breve così l'intera gamma di movimento sopravvive anche se la velocità di riproduzione viene compressa.

1 — campiona ~14 fotogrammi in modo uniforme dalla sorgente, ritagliati/scalati in base al layout:

```bash
# layout frame: adattato con letterbox in MIDDLE_BOX, quindi basta ridimensionare (nessun ritaglio necessario)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# layout fullscreen: stirato per riempire 240x240, quindi ritaglia prima a quadrato o si deformerà
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = numero di fotogrammi della sorgente ÷ 14 (arrotondato per difetto) — usa ffprobe sulla sorgente (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`) per ottenerlo.

2 — ricodifica i fotogrammi campionati con un loop breve (10fps = 100ms/fotogramma ≈ 1,4s di loop per 14 fotogrammi) e una tavolozza piccola:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Ancora oltre 300 KB? Riduci `max_colors` a 32 (prova anche `dither=none`) prima di tagliare il numero di fotogrammi — è quello il vero costo del loop.



`custom` legge `display.gifs` da `config.json`. Ogni voce host è una stringa di percorso (una GIF per tutti gli stati) oppure una mappa per stato; `"default"` è il fallback. Qualsiasi voce può anche essere `{"path": ..., "layout": "fullscreen"}` per andare a schermo intero per quella:

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

Ordine di risoluzione per ogni push: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → segnaposto hosts in bundle. Una GIF mancante o illeggibile non fa mai diventare nero lo schermo — ricade sul fotogramma statico.

## Comandi

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Onboarding completo — individua il dispositivo, verifica il firmware, salva l'IP, esegue il backup, prende il controllo |
| `/agent-glance:status` | Controllo di stato — raggiungibilità, tema attivo, hook duplicati, log degli errori |
| `/agent-glance:test` | Invia un fotogramma (o li fa scorrere tutti e tre) per verificare il rendering |
| `/agent-glance:theme` | Sbircia gli schermi nativi del dispositivo — meteo, previsioni, orologi (Ultra; il monitor torna alla prossima attività) |
| `/agent-glance:restore` | Riporta il dispositivo al suo orologio e alle foto originali |

Alcune opzioni sono **solo flag CLI** (nessun comando slash) — vengono salvate in `~/.agent-glance/config.json`, come `--ip`:

| Flag | Cosa fa |
|---|---|
| `--ip <IP>` | salva l'IP del dispositivo |
| `--preset default\|hosts\|custom` | cambia modalità di visualizzazione (vedi [Modalità GIF](#modalità-gif-e-preset)) |
| `--layout frame\|fullscreen` | layout modalità gif (frame mantiene header+footer; fullscreen è solo GIF) |
| `--test [state] [subtitle]` | invia un fotogramma; rispetta il preset corrente, quindi fa l'anteprima anche della modalità gif |

## Come funziona

Questo firmware **non ha un'API testuale**, quindi non c'è nulla da "stampare". Lo script renderizza invece una GIF 240×240 con Pillow e la carica nell'album foto del dispositivo, rendendo quell'immagine l'unica foto abilitata e Photo l'unico tema abilitato — così il fotogramma resta fisso invece di ruotare via. Anche il decodificatore GIF del firmware riproduce GIF **animate**, quindi in modalità gif lo script compone una GIF multi-fotogramma e il dispositivo la riproduce in loop localmente — un caricamento per stato, nessun traffico per fotogramma.

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

## Riferimento API del dispositivo (SmallTV Ultra, firmware stock)

Temi: 1 Orologio meteo di oggi · 2 Previsioni · **3 Album foto** · 4–6 Stili orologio · 7 Orologio meteo semplice.

| Action | Endpoint |
|---|---|
| caricare un'immagine | `POST /doUpload?dir=/image/` (campo multipart `image`; la ricarica con lo stesso nome sovrascrive) |
| fissare a schermo | `GET /set?img=/image/<f>` (codificato URL; richiede il tema 3) |
| cambiare tema | `GET /set?theme=<n>` |
| flag dei temi | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| eliminare un file | `GET /delete?file=/image/<f>` |
| leggere lo stato | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

Incid scoperti sondando un dispositivo reale:

- L'immagine mostrata è *fissata* da `/set?img=` — gli altri file dell'album restano ma non ruotano mai (niente flag per foto come su SD_RU; setup non li tocca).
- Le GIF animate vengono decodificate e ripetute in locale; l'intero filesystem da 3 MB è condiviso con le risorse meteo/orologio, quindi tenete le GIF piccole (~1 MB liberi da nuovo).
- `/set?img=` e `/set?theme=` restituiscono il testo letterale `OK`, non JSON.
- ⚠️ stessa postura di fiducia di SD_RU: ogni endpoint è senza autenticazione sulla LAN.

## Limitazioni

- **I 7 temi del dispositivo non possono mostrare ciascuno una sessione.** Solo il tema Photo renderizza contenuti personalizzati; gli altri sei sono interfacce fisse di orologio/meteo. Far ruotare più sessioni richiederebbe più immagini nell'album — non è implementato.
- Le metriche provengono dal formato di trascrizione di Claude Code. Su Codex/agy i colori di stato funzionano comunque, ma i campi modello/token possono restare vuoti.
- Lo stato (`config.json`, `device_backup.json`) risiede in `~/.agent-glance/`, non nella directory del plugin, quindi non viene cancellato negli aggiornamenti del plugin.

## Licenza

[MIT](../../../LICENSE)
