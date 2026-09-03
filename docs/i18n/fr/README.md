<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | **[Français](README.md)** | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> Transforme une **GeekMagic SmallTV** en écran d'état d'agent en direct — pour Claude Code, Codex et agy.

Le petit écran affiche ce que votre agent est en train de faire : **WORKING**, **APPROVAL NEEDED** ou **DONE** — ainsi que le modèle, l'utilisation de la fenêtre de contexte et le nombre de tokens, extraits en direct de la transcription de session.
La fonctionnalité phare est l'écran rouge **APPROVAL** : placez l'agent sur un autre moniteur et vous pourrez vous éloigner, y jeter un œil et savoir à l'instant où il attend votre approbation, plutôt que de le découvrir dix minutes plus tard.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (ambre) + le prompt |
| approval needed | ⛔ **APPROVAL** (rouge) + ce qui est demandé |
| turn finished | ✓ **DONE** (vert) |

Chaque image affiche aussi `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## À qui est-ce destiné ?

- **Vous lancez de longues sessions d'agent** — migrations, suites de tests, gros refactors — et vous vérifiez sans cesse le terminal pour voir si c'est fini ou bloqué.
- **Vous vous éloignez du clavier** — et vous voulez savoir à *l'instant* où l'agent attend votre approbation, pas dix minutes plus tard.
- **Vous utilisez Claude Code / Codex / agy / hermes** en mode headless et regrettez le retour visuel qu'offrirait un IDE complet.
- **Vous possédez une GeekMagic SmallTV** qui prend la poussière et vous voulez qu'elle se rende enfin utile.

Si vous êtes déjà revenu au terminal en pensant *"attends, ça fait tout ce temps qu'il m'attend ?"* — c'est pour vous.

## Prérequis

- Une GeekMagic SmallTV sous l'un des firmwares pris en charge (détecté automatiquement et enregistré via `--ip`) :
  - **SD_RU / SD Pro** firmware communautaire (ESP8266) — vérification rapide — cette commande doit renvoyer du JSON avec un tableau `files` :

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra firmware d'origine** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — vérification rapide — cette commande doit renvoyer du JSON avec une clé `theme` :

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  Les autres variantes du firmware d'origine GeekMagic et la « PRO » ESP32 exposent une API *différente* et ne sont **pas** prises en charge.

- L'appareil doit être sur le même Wi-Fi que cette machine.
- Python 3.8+ avec Pillow (`pip install Pillow`).

## Installation

Installation autonome depuis ce dépôt — embarque le marketplace `agent-glance` éponyme ; sans hub.

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

### Ce que chaque hôte obtient

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | vérifié de bout en bout |
| Codex | ✅ | ✅ | ✅ | le fichier de hooks correspond au schéma documenté ; non vérifié à l'exécution |
| agy | ✅ | — | ✅ | le format de hooks correspond à un plugin agy réellement installé ; non vérifié à l'exécution |
| hermes | ✅ | — | ❌ | skills uniquement — hermes s'enregistre via `register(ctx)`, sans hooks de cycle de vie connectés |
| Grok Build | ✅ | ✅ | ✅ | le fichier de hooks suit le schéma compatible Claude ; non vérifié à l'exécution |

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
| `AGENT_GLANCE_PRESET` | preset d'affichage : `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | disposition du mode gif : `frame` \| `fullscreen` | `frame` |

### Mode GIF et presets

> [!WARNING]
> **Avertissement sur la taille des GIF** : Les fichiers GIF volumineux sollicitent fortement la mémoire de l'appareil (RAM/Flash de l'ESP8266) et peuvent provoquer des redémarrages ou des plantages inattendus. Veillez à maintenir vos fichiers sous **< 100 KB**.

Le mode par défaut est l'image statique décrite ci-dessus. Choisir un autre preset bascule en **mode gif**, qui compose un GIF animé en boucle (personnage au centre, en-tête + pied de page d'état conservés) lu localement par l'appareil — un envoi par état, pas de trafic réseau par image. L'état reste signalé par la barre d'accent en haut + la couleur de fond.

| Preset | Ce qu'il affiche |
|---|---|
| `default` | Image statique (le comportement d'origine) |
| `hosts` | Un GIF de personnage par hôte, fourni avec le plugin, au centre ; en-tête + pied de page conservés |
| `custom` | Vos propres GIFs, par hôte et/ou par état (voir le schéma) |

Choisissez un preset avec le flag CLI `--preset` (il persiste dans `config.json`, comme `--ip`) :

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` est livré avec des placeholders neutres dans `assets/gif/` afin de fonctionner immédiatement. Pour utiliser votre propre personnage, déposez un GIF dans le répertoire utilisateur — il prend le pas sur celui fourni, et l'écran se met à jour au prochain envoi d'état (pas de redémarrage) :

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

Nommez le fichier d'après l'hôte qu'il doit remplacer (minuscules, espaces → tirets) :

| Hôte détecté | Fichier de remplacement |
|---|---|
| Claude Code | `claude-code.gif` |
| Codex | `codex.gif` |
| Antigravity | `antigravity.gif` |
| Hermes | `hermes.gif` |
| tout autre hôte | `agent.gif` |

### Spécifications GIF optimales

| Paramètre | Mise en page `frame` | Mise en page `fullscreen` |
|---|---|---|
| **Résolution optimale** | **224 × 116 px** (~1,93:1) ou **116 × 116 px** (1:1) | **240 × 240 px** (carré 1:1) |
| **Cible de composition** | S'insère dans `MIDDLE_BOX = (8, 46, 224, 116)` | Couvre tout l'écran 1.54" du SmallTV |
| **Taille de fichier recommandée** | **< 100 KB** (Maximum strict < 300 KB pour éviter les plantages RAM/OOM et redémarrages ESP8266) |
| **Nombre d'images** | **12 – 16 images** (le moteur de rendu sous-échantillonne au-delà de `_MAX_FRAMES = 16`) |
| **Délai d'image** | **80ms – 150ms** par image (boucle de 1.2s – 2.0s) |
| **Palette de couleurs** | **64 – 128 couleurs** (optimise la vitesse de rendu et l'usure de la mémoire Flash) |

**Réduire un GIF source à la spécification** (les exports bruts dépassent facilement plusieurs Mo) : échantillonner des images uniformément sur tout le clip, puis réencoder avec une boucle courte pour préserver toute l'amplitude du mouvement même si la vitesse de lecture est compressée.

1 — échantillonner ~14 images uniformément depuis la source, recadrées/redimensionnées selon la mise en page :

```bash
# mise en page frame : incrustée en letterbox dans MIDDLE_BOX, donc juste réduire l'échelle (pas besoin de recadrer)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# mise en page fullscreen : étirée pour remplir 240x240, donc recadrer en carré d'abord sinon ça déforme
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = nombre d'images de la source ÷ 14 (arrondi à l'inférieur) — utiliser ffprobe sur la source (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`) pour l'obtenir.

2 — réencoder les images échantillonnées avec une boucle courte (10fps = 100ms/image ≈ 1,4s de boucle pour 14 images) et une petite palette :

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Toujours au-dessus de 300 KB ? Réduire `max_colors` à 32 (essayer aussi `dither=none`) avant de réduire le nombre d'images — c'est ce qui coûte réellement cher dans la boucle.



`custom` lit `display.gifs` dans `config.json`. Chaque entrée d'hôte est soit une chaîne de chemin (un seul GIF pour tous les états), soit une map par état ; `"default"` est le fallback. Chaque entrée peut aussi être `{"path": ..., "layout": "fullscreen"}` pour passer en plein écran sur celle-là :

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

Ordre de résolution à chaque envoi : `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → placeholder hosts fourni. Un GIF manquant ou illisible ne vide jamais l'écran — il retombe sur l'image statique.

## Commandes

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Intégration complète — détecte l'appareil, vérifie le firmware, enregistre l'IP, sauvegarde, prend le contrôle |
| `/agent-glance:status` | Vérification d'état — accessibilité, thème actif, hooks dupliqués, journal d'erreurs |
| `/agent-glance:test` | Envoie une image (ou fait défiler les trois) pour vérifier le rendu |
| `/agent-glance:theme` | Aperçu des écrans natifs de l'appareil — météo, prévisions, horloges (Ultra ; le moniteur revient à la prochaine activité) |
| `/agent-glance:restore` | Remet l'appareil dans son état d'horloge et de photos d'origine |

Quelques options sont **des flags CLI uniquement** (pas de commande slash) — elles persistent dans `~/.agent-glance/config.json`, comme `--ip` :

| Flag | Ce qu'elle fait |
|---|---|
| `--ip <IP>` | enregistre l'IP de l'appareil |
| `--preset default\|hosts\|custom` | bascule le mode d'affichage (voir [Mode GIF](#mode-gif-et-presets)) |
| `--layout frame\|fullscreen` | disposition du mode gif (`frame` conserve en-tête+pied de page ; `fullscreen` = GIF uniquement) |
| `--test [state] [subtitle]` | envoie une image ; respecte le preset courant, donc prévisualise aussi le mode gif |

## Fonctionnement

Ce firmware n'a **pas d'API texte**, il n'y a donc rien à "afficher" à proprement parler. Le script génère à la place un GIF 240×240 avec Pillow et le télécharge dans l'album photo de l'appareil, en faisant de cette image la seule photo activée et de Photo le seul thème activé — de sorte que l'image reste fixe au lieu de tourner. Le décodeur GIF du firmware lit aussi les GIFs **animés**, donc en mode gif le script compose un GIF multi-frames que l'appareil lit en boucle localement — un envoi par état, pas de trafic par image.

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

## Référence de l'API de l'appareil (SmallTV Ultra, firmware d'origine)

Thèmes : 1 Horloge météo du jour · 2 Prévisions · **3 Album photo** · 4–6 Styles d'horloge · 7 Horloge météo simple.

| Action | Endpoint |
|---|---|
| envoyer une image | `POST /doUpload?dir=/image/` (champ multipart `image` ; un renvoi sous le même nom écrase l'original) |
| épingler à l'écran | `GET /set?img=/image/<f>` (encodé URL ; nécessite le thème 3) |
| changer de thème | `GET /set?theme=<n>` |
| indicateurs de thèmes | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| supprimer un fichier | `GET /delete?file=/image/<f>` |
| lire l'état | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

Pièges découverts en sondant un appareil réel :

- L'image affichée est *épinglée* par `/set?img=` — les autres fichiers de l'album restent mais ne tournent jamais (pas d'indicateurs par photo comme SD_RU ; setup n'y touche pas).
- Les GIF animés sont décodés et bouclés localement ; tout le système de 3 Mo est partagé avec les ressources météo/horloge, gardez donc les GIF petits (~1 Mo libre d'origine).
- `/set?img=` et `/set?theme=` renvoient le littéral `OK`, pas du JSON.
- ⚠️ même posture de confiance que SD_RU : chaque endpoint est non authentifié sur le LAN.

## Limitations

- **Les 7 thèmes de l'appareil ne peuvent pas chacun afficher une session.** Seul le thème Photo affiche du contenu personnalisé ; les six autres sont des interfaces fixes d'horloge/météo. Faire tourner plusieurs sessions nécessiterait plusieurs images dans l'album — ce n'est pas implémenté.
- Les métriques proviennent du format de transcription de Claude Code. Sous Codex/agy, les couleurs d'état fonctionnent toujours, mais les champs modèle/tokens peuvent rester vides.
- L'état (`config.json`, `device_backup.json`) réside dans `~/.agent-glance/`, pas dans le répertoire du plugin, et n'est donc pas effacé lors des mises à jour du plugin.

## Licence

[MIT](../../../LICENSE)
