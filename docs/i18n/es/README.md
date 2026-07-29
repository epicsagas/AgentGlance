<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | **[Español](README.md)** | [Français](../fr/README.md) | [Deutsch](../de/README.md) | [Português](../pt/README.md) | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<center>
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</center>

> Convierte una **GeekMagic SmallTV** en una pantalla de estado en vivo para tu agente — para Claude Code, Codex y agy.

La pequeña pantalla muestra lo que tu agente está haciendo en este momento: **WORKING**, **APPROVAL NEEDED** o **DONE** — además del modelo, el uso de la ventana de contexto y el recuento de tokens, extraídos de la transcripción de sesión en vivo.
La joya de la corona es la pantalla roja de **APPROVAL**: coloca el agente en otro monitor y podrás alejarte, echar un vistazo y saber en el instante en que se queda esperando tu aprobación, en lugar de descubrirlo diez minutos después.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (ámbar) + el prompt |
| approval needed | ⛔ **APPROVAL** (rojo) + lo que solicita |
| turn finished | ✓ **DONE** (verde) |

Cada fotograma también incluye `model · context bar + % · in/out tokens`.

<center>
<img width="49%" src="../../../assets/claude-approval.jpeg" alter="claude approval">
<img width="49%" src="../../../assets/claude-done.jpeg" alter="claude approval">
</center>

## Requisitos

- Una GeekMagic SmallTV con firmware comunitario **SD_RU / SD Pro** (ESP8266). Comprobación rápida — esto debe devolver JSON con un array `files`:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  El firmware oficial de GeekMagic y el "PRO" basado en ESP32 exponen una API *distinta* y **no son compatibles**.
  
- El dispositivo debe estar en la misma red Wi-Fi que esta máquina.
- Python 3.8+ con Pillow (`pip install Pillow`).

## Instalación

Se distribuye a través del marketplace [`epicsagas/plugins`](https://github.com/epicsagas/plugins); el plugin en sí vive en [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

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

### Qué obtiene cada host

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | verificado de extremo a extremo |
| Codex | ✅ | ✅ | ✅ | el archivo de hooks coincide con el esquema documentado; sin verificar en ejecución |
| agy | ✅ | — | ✅ | el formato de hooks coincide con un plugin de agy realmente instalado; sin verificar en ejecución |
| hermes | ✅ | — | ❌ | solo skills — hermes se registra mediante `register(ctx)`, sin hooks de ciclo de vida conectados |

Luego incorpora el dispositivo — esto lo encuentra, guarda la IP, hace una copia de seguridad del dispositivo y lo cambia al modo monitor:

```
/agent-glance:setup
```

En hosts sin comandos de barra, ejecuta los mismos pasos a mano:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Los hooks vienen incluidos con el plugin y se activan por sí solos. **Reinicia el agente después de instalar** — los hooks se cargan al inicio de la sesión.

## Configuración

La configuración se lee **primero desde variables de entorno**, y si no existen recurre a `~/.agent-glance/config.json` (escrito por `--ip`). La variable de entorno es la opción más portable para configuraciones compartidas o multi-máquina.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | IP del dispositivo — **obligatorio** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | ventana de contexto usada para escalar la barra de % | `200000` |

## Comandos

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Incorporación completa — descubre el dispositivo, verifica el firmware, guarda la IP, hace copia de seguridad, toma el control |
| `/agent-glance:status` | Comprobación de estado — accesibilidad, tema activo, hooks duplicados, registro de errores |
| `/agent-glance:test` | Envía un fotograma (o recorre los tres) para comprobar el renderizado |
| `/agent-glance:restore` | Devuelve el dispositivo a su reloj y fotos originales |

## Cómo funciona

El firmware **no tiene API de texto**, así que no hay nada que "imprimir". En su lugar, el script renderiza un GIF de 240×240 con Pillow y lo sube al álbum de fotos del dispositivo, dejando esa imagen como la única foto habilitada y Photo como el único tema habilitado — de modo que el fotograma se queda fijo en lugar de rotar.

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

## Hooks multi-host

Los tres hosts **no** comparten un formato de hooks, así que cada uno tiene su propio archivo. Deliberadamente no existe un `hooks/hooks.json` genérico — esa ruta es la predeterminada tanto para Claude Code como para Codex, y dejar uno ahí haría que el host equivocado lo cargue.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | declarado en `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | declarado en `.codex-plugin/plugin.json` |
| agy | `hooks.json` (**raíz** del plugin) | forzado — el esquema de manifiesto de agy es `additionalProperties:false`, así que la ruta no se puede declarar |

Como los hosts exponen ciclos de vida distintos, los eventos también difieren:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

Y los payloads difieren: Claude Code y Codex envían `hook_event_name` / `transcript_path` (snake_case); agy envía `hookEventName` / `transcriptPath` (camelCase) y envuelve su configuración en un grupo de hooks con nombre. El script normaliza todo esto.

Solo Claude Code sustituye `${CLAUDE_PLUGIN_ROOT}` dentro de los comandos de hook, así que los otros dos referencian directamente la ruta de su propio plugin instalado:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Referencia de la API del dispositivo (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Peculiaridades descubiertas al examinar un dispositivo real:

- `state` debe ser `1` / `0`. El firmware ejecuta `atoi()` sobre él, así que `"true"` se convierte en `0` y hace silenciosamente lo contrario de lo que se pretendía.
- Deshabilitar el *último* tema o foto habilitado devuelve **HTTP 403** — una protección contra pantalla en blanco. La configuración habilita primero el objetivo y luego deshabilita el resto.
- El ESP8266 es de un solo hilo y devuelve 403 cuando está ocupado con una solicitud anterior, así que las subidas reintentan.
- ⚠️ `/config` expone la contraseña Wi-Fi del dispositivo y la clave de la API del clima **en texto plano y sin autenticación**. Eso es comportamiento del firmware, no algo que añada este plugin — pero trata el dispositivo como no confiable en una red compartida.

## Limitaciones

- **Los 7 temas del dispositivo no pueden mostrar cada uno una sesión.** Solo el tema Photo renderiza contenido personalizado; los otros seis son interfaces fijas de reloj/clima. Rotar varias sesiones implicaría varias imágenes en el álbum — no está implementado.
- Las métricas provienen del formato de transcripción de Claude Code. Bajo Codex/agy los colores de estado siguen funcionando, pero los campos de modelo/tokens pueden quedar en blanco.
- El estado (`config.json`, `device_backup.json`) vive en `~/.agent-glance/`, no en el directorio del plugin, por lo que no se borra al actualizar el plugin.

## Licencia

[MIT](../../../LICENSE)
