<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | **[Português](README.md)** | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<center>
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</center>

> Transforma uma **GeekMagic SmallTV** em uma tela de status do agente em tempo real — para Claude Code, Codex e agy.

A telinha mostra o que o seu agente está fazendo agora: **WORKING**, **APPROVAL NEEDED** ou **DONE** — além do modelo, do uso da janela de contexto e da contagem de tokens, extraídos ao vivo da transcrição da sessão.
O recurso mais forte é a tela vermelha de **APPROVAL**: coloque o agente em outro monitor e você pode se afastar, dar uma olhada rápida e saber no mesmo instante que ele está travado esperando sua aprovação, em vez de descobrir isso dez minutos depois.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (âmbar) + o prompt |
| approval needed | ⛔ **APPROVAL** (vermelho) + o que está sendo pedido |
| turn finished | ✓ **DONE** (verde) |

Cada quadro também traz `model · context bar + % · in/out tokens`.

<center>
<img width="49%" src="../../../assets/claude-approval.jpeg" alter="claude approval">
<img width="49%" src="../../../assets/claude-done.jpeg" alter="claude approval">
</center>

## Requisitos

- Uma GeekMagic SmallTV com firmware comunitário **SD_RU / SD Pro** (ESP8266). Verificação rápida — isto deve retornar JSON com um array `files`:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  O firmware oficial da GeekMagic e o "PRO" baseado em ESP32 expõem uma API *diferente* e **não são suportados**.
  
- O dispositivo precisa estar na mesma rede Wi-Fi que esta máquina.
- Python 3.8+ com Pillow (`pip install Pillow`).

## Instalação

Distribuído pelo marketplace [`epicsagas/plugins`](https://github.com/epicsagas/plugins); o plugin em si vive em [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

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

### O que cada host oferece

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | verificado de ponta a ponta |
| Codex | ✅ | ✅ | ✅ | o arquivo de hooks corresponde ao esquema documentado; não verificado em tempo de execução |
| agy | ✅ | — | ✅ | o formato de hooks corresponde a um plugin agy realmente instalado; não verificado em tempo de execução |
| hermes | ✅ | — | ❌ | apenas skills — o hermes se registra via `register(ctx)`, sem hooks de ciclo de vida conectados |

Em seguida, integre o dispositivo — isso o encontra, salva o IP, faz backup do dispositivo e o alterna para o modo monitor:

```
/agent-glance:setup
```

Em hosts sem comandos de barra, execute as mesmas etapas manualmente:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Os hooks vêm junto com o plugin e se ativam sozinhos. **Reinicie o agente após instalar** — os hooks são carregados no início da sessão.

## Configuração

A configuração é lida **primeiro via variáveis de ambiente**, recorrendo a `~/.agent-glance/config.json` (escrito por `--ip`) caso não existam. A variável de ambiente é a opção mais portátil para configurações compartilhadas ou com várias máquinas.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | IP do dispositivo — **obrigatório** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | janela de contexto usada para escalar a barra de % | `200000` |

## Comandos

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Integração completa — descobre o dispositivo, verifica o firmware, salva o IP, faz backup, assume o controle |
| `/agent-glance:status` | Verificação de saúde — acessibilidade, tema ativo, hooks duplicados, log de erros |
| `/agent-glance:test` | Envia um quadro (ou percorre os três) para verificar a renderização |
| `/agent-glance:restore` | Devolve o dispositivo ao seu relógio e fotos originais |

## Como funciona

Esse firmware **não tem API de texto**, então não há nada para "imprimir". Em vez disso, o script renderiza um GIF de 240×240 com Pillow e o envia para o álbum de fotos do dispositivo, tornando essa imagem a única foto habilitada e o Photo o único tema habilitado — assim o quadro fica fixo em vez de girar para outro tema.

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

Os três hosts **não** compartilham um formato de hooks, então cada um tem seu próprio arquivo. Deliberadamente não existe um `hooks/hooks.json` genérico — esse caminho é o padrão tanto para o Claude Code quanto para o Codex, e deixar um ali faria com que o host errado o carregasse.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | declarado em `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | declarado em `.codex-plugin/plugin.json` |
| agy | `hooks.json` (**raiz** do plugin) | forçado — o esquema de manifesto do agy é `additionalProperties:false`, então o caminho não pode ser declarado |

Como os hosts expõem ciclos de vida diferentes, os eventos também diferem:

| Display | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

E os payloads diferem: Claude Code e Codex enviam `hook_event_name` / `transcript_path` (snake_case); agy envia `hookEventName` / `transcriptPath` (camelCase) e envolve sua configuração em um grupo de hooks nomeado. O script normaliza tudo isso.

Somente o Claude Code substitui `${CLAUDE_PLUGIN_ROOT}` dentro dos comandos de hook, então os outros dois referenciam diretamente o caminho do próprio plugin instalado:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Referência da API do dispositivo (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Peculiaridades encontradas ao investigar um dispositivo real:

- `state` precisa ser `1` / `0`. O firmware executa `atoi()` sobre ele, então `"true"` vira `0` e silenciosamente faz o oposto do pretendido.
- Desabilitar o *último* tema ou foto habilitado retorna **HTTP 403** — uma proteção contra tela em branco. A configuração habilita primeiro o alvo e depois desabilita o restante.
- O ESP8266 é single-threaded e retorna 403 quando está ocupado com uma requisição anterior, então os uploads tentam novamente.
- ⚠️ `/config` expõe a senha de Wi-Fi do dispositivo e a chave da API de clima **em texto puro e sem autenticação**. Isso é comportamento do firmware, não algo adicionado por este plugin — ainda assim, trate o dispositivo como não confiável em uma rede compartilhada.

## Limitações

- **Os 7 temas do dispositivo não podem exibir uma sessão cada um.** Somente o tema Photo renderiza conteúdo personalizado; os outros seis são interfaces fixas de relógio/clima. Alternar entre várias sessões exigiria várias imagens no álbum — isso não está implementado.
- As métricas vêm do formato de transcrição do Claude Code. No Codex/agy as cores de estado continuam funcionando, mas os campos de modelo/tokens podem ficar em branco.
- O estado (`config.json`, `device_backup.json`) fica em `~/.agent-glance/`, não no diretório do plugin, portanto não é apagado em atualizações do plugin.

## Licença

[MIT](../../../LICENSE)
