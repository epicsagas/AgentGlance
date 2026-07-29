<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | **[Français](README.md)** | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<center>
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</center>

> Transforme une **GeekMagic SmallTV** en écran d'état d'agent en direct — pour Claude Code, Codex et agy.

Le petit écran affiche ce que votre agent est en train de faire : **WORKING**, **APPROVAL NEEDED** ou **DONE** — ainsi que le modèle, l'utilisation de la fenêtre de contexte et le nombre de tokens, extraits en direct de la transcription de session.
La fonctionnalité phare est l'écran rouge **APPROVAL** : placez l'agent sur un autre moniteur et vous pourrez vous éloigner, y jeter un œil et savoir à l'instant où il attend votre approbation, plutôt que de le découvrir dix minutes plus tard.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (ambre) + le prompt |
| approval needed | ⛔ **APPROVAL** (rouge) + ce qui est demandé |
| turn finished | ✓ **DONE** (vert) |

Chaque image affiche aussi `model · context bar + % · in/out tokens`.

<center>
<img width="49%" src="../../../assets/claude-approval.jpeg" alter="claude approval">
<img width="49%" src="../../../assets/claude-done.jpeg" alter="claude approval">
</center>

## Prérequis

- Une GeekMagic SmallTV sous firmware communautaire **SD_RU / SD Pro** (ESP8266). Vérification rapide — ceci doit renvoyer du JSON contenant un tableau `files` :

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  Le firmware d'origine GeekMagic et le "PRO" à base d'ESP32 exposent une API *différente* et **ne sont pas pris en charge**.
  
- L'appareil doit être sur le même Wi-Fi que cette machine.
- Python 3.8+ avec Pillow (`pip install Pillow`).

## Installation

Distribué via la marketplace [`epicsagas/plugins`](https://github.com/epicsagas/plugins) ; le plugin lui-même se trouve dans [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

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

### Ce que chaque hôte obtient

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | vérifié de bout en bout |
| Codex | ✅ | ✅ | ✅ | le fichier de hooks correspond au schéma documenté ; non vérifié à l'exécution |
| agy | ✅ | — | ✅ | le format de hooks correspond à un plugin agy réellement installé ; non vérifié à l'exécution |
| hermes | ✅ | — | ❌ | skills uniquement — hermes s'enregistre via `register(ctx)`, sans hooks de cycle de vie connectés |

Intégrez ensuite l'appareil — cela le détecte, enregistre l'IP, sauvegarde l'appareil et le bascule en mode moniteur :

```
/agent-glance:setup
```

Sur les hôtes sans commandes slash, exécutez les mêmes étapes à la main :

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Les hooks sont fournis avec le plugin et s'activent d'eux-mêmes. **Redémarrez l'agent après l'installation** — les hooks sont chargés au démarrage de la session.

## Configuration

La configuration est lue **d'abord via les variables d'environnement**, puis retombe sur `~/.agent-glance/config.json` (écrit par `--ip`) si elles sont absentes. La variable d'environnement est l'option la plus portable pour les configurations partagées ou multi-machines.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | IP de l'appareil — **obligatoire** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | fenêtre de contexte utilisée pour mettre à l'échelle la barre de % | `200000` |

## Commandes

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Intégration complète — détecte l'appareil, vérifie le firmware, enregistre l'IP, sauvegarde, prend le contrôle |
| `/agent-glance:status` | Vérification d'état — accessibilité, thème actif, hooks dupliqués, journal d'erreurs |
| `/agent-glance:test` | Envoie une image (ou fait défiler les trois) pour vérifier le rendu |
| `/agent-glance:restore` | Remet l'appareil dans son état d'horloge et de photos d'origine |

## Fonctionnement

Ce firmware n'a **pas d'API texte**, il n'y a donc rien à "afficher" à proprement parler. Le script génère à la place un GIF 240×240 avec Pillow et le télécharge dans l'album photo de l'appareil, en faisant de cette image la seule photo activée et de Photo le seul thème activé — de sorte que l'image reste fixe au lieu de tourner.

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

## Hooks multi-hôtes

Les trois hôtes ne partagent **pas** le même format de hooks, chacun a donc son propre fichier. Il n'existe volontairement pas de `hooks/hooks.json` générique — ce chemin est celui par défaut à la fois pour Claude Code et Codex, et en laisser un à cet endroit ferait que le mauvais hôte le charge.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | déclaré dans `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | déclaré dans `.codex-plugin/plugin.json` |
| agy | `hooks.json` (**racine** du plugin) | forcé — le schéma de manifeste d'agy est `additionalProperties:false`, donc le chemin ne peut pas être déclaré |

Comme les hôtes exposent des cycles de vie différents, les événements diffèrent aussi :

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

Et les payloads diffèrent : Claude Code et Codex envoient `hook_event_name` / `transcript_path` (snake_case) ; agy envoie `hookEventName` / `transcriptPath` (camelCase) et enveloppe sa configuration dans un groupe de hooks nommé. Le script normalise tout cela.

Seul Claude Code substitue `${CLAUDE_PLUGIN_ROOT}` dans les commandes de hook, donc les deux autres référencent directement le chemin de leur propre plugin installé :

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Référence de l'API de l'appareil (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Particularités découvertes en sondant un appareil réel :

- `state` doit être `1` / `0`. Le firmware exécute `atoi()` dessus, donc `"true"` devient `0` et fait silencieusement le contraire de ce qui était voulu.
- Désactiver le *dernier* thème ou la dernière photo activée renvoie **HTTP 403** — une protection contre l'écran noir. La configuration active d'abord la cible, puis désactive le reste.
- L'ESP8266 est monothread et renvoie 403 lorsqu'il est occupé par une requête précédente, donc les envois réessaient.
- ⚠️ `/config` expose le mot de passe Wi-Fi de l'appareil et la clé de l'API météo **en clair et sans authentification**. C'est le comportement du firmware, pas quelque chose ajouté par ce plugin — mais traitez l'appareil comme non fiable sur un réseau partagé.

## Limitations

- **Les 7 thèmes de l'appareil ne peuvent pas chacun afficher une session.** Seul le thème Photo affiche du contenu personnalisé ; les six autres sont des interfaces fixes d'horloge/météo. Faire tourner plusieurs sessions nécessiterait plusieurs images dans l'album — ce n'est pas implémenté.
- Les métriques proviennent du format de transcription de Claude Code. Sous Codex/agy, les couleurs d'état fonctionnent toujours, mais les champs modèle/tokens peuvent rester vides.
- L'état (`config.json`, `device_backup.json`) réside dans `~/.agent-glance/`, pas dans le répertoire du plugin, et n'est donc pas effacé lors des mises à jour du plugin.

## Licence

[MIT](../../../LICENSE)
