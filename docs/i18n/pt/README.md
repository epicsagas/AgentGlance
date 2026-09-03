<!-- Translated from README.md @ commit 58cc9a2 (2026-07-29) -->
<!-- If English README has changed since then, this translation may be outdated -->

> This is a translation of [README.md](../../../README.md).
> The English version is the authoritative source and may be more up-to-date.

[English](../../../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](../zh-Hans/README.md) | [繁體中文](../zh-Hant/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | **[Português](README.md)** | [Русский](../ru/README.md) | [Italiano](../it/README.md)

<div align="center">
<img width="320px" src="../../../assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>
</div>

> Transforma uma **GeekMagic SmallTV** em uma tela de status do agente em tempo real — para Claude Code, Codex e agy.

A telinha mostra o que o seu agente está fazendo agora: **WORKING**, **APPROVAL NEEDED** ou **DONE** — além do modelo, do uso da janela de contexto e da contagem de tokens, extraídos ao vivo da transcrição da sessão.
O recurso mais forte é a tela vermelha de **APPROVAL**: coloque o agente em outro monitor e você pode se afastar, dar uma olhada rápida e saber no mesmo instante que ele está travado esperando sua aprovação, em vez de descobrir isso dez minutos depois.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (âmbar) + o prompt |
| approval needed | ⛔ **APPROVAL** (vermelho) + o que está sendo pedido |
| turn finished | ✓ **DONE** (verde) |

Cada quadro também traz `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="../../../assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="../../../assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## Para quem é isto?

- **Você roda sessões longas do agente** — migrações, suítes de testes, grandes refatorações — e fica conferindo o terminal pra ver se terminou ou travou.
- **Você se afasta do teclado** — e quer saber no *momento* exato em que o agente precisa da sua aprovação, e não dez minutos depois.
- **Você usa Claude Code / Codex / agy / hermes** em modo headless e sente falta do feedback visual que uma IDE completa daria.
- **Você tem uma GeekMagic SmallTV** parada e quer que ela puxe seu peso de verdade.

Se você já voltou pro terminal e pensou *"espera, ele ficou me esperando o tempo todo?"* — isto é pra você.

## Requisitos

- Uma GeekMagic SmallTV com qualquer um dos firmwares suportados (detetado automaticamente e guardado com `--ip`):
  - **SD_RU / SD Pro** firmware da comunidade (ESP8266) — verificação rápida — este comando deve devolver JSON com um array `files`:

    ```bash
    curl -s http://<DEVICE_IP>/photo/list
    ```

  - **SmallTV Ultra firmware de fábrica** (ESP32, [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra)) — verificação rápida — este comando deve devolver JSON com uma chave `theme`:

    ```bash
    curl -s http://<DEVICE_IP>/app.json
    ```

  Outras variantes do firmware de fábrica da GeekMagic e a "PRO" ESP32 usam uma API *diferente* e **não** são suportadas.

- O dispositivo precisa estar na mesma rede Wi-Fi que esta máquina.
- Python 3.8+ com Pillow (`pip install Pillow`).

## Instalação

Instalação autônoma a partir deste repositório — traz o marketplace `agent-glance` de mesmo nome; sem hub.

**Grok Build (xAI)**

```bash
grok plugin marketplace add epicsagas/AgentGlance
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

### O que cada host oferece

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | verificado de ponta a ponta |
| Codex | ✅ | ✅ | ✅ | o arquivo de hooks corresponde ao esquema documentado; não verificado em tempo de execução |
| agy | ✅ | — | ✅ | o formato de hooks corresponde a um plugin agy realmente instalado; não verificado em tempo de execução |
| hermes | ✅ | — | ❌ | apenas skills — o hermes se registra via `register(ctx)`, sem hooks de ciclo de vida conectados |
| Grok Build | ✅ | ✅ | ✅ | o arquivo de hooks segue o esquema compatível com Claude; não verificado em execução |

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
| `AGENT_GLANCE_PRESET` | predefinição de exibição: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | layout do modo gif: `frame` \| `fullscreen` | `frame` |

### Modo GIF e predefinições

> [!WARNING]
> **Aviso sobre o tamanho do GIF**: Arquivos GIF grandes causam uma forte sobrecarga na memória do dispositivo (RAM/Flash do ESP8266) e podem provocar reinicializações ou falhas inesperadas. Mantenha seus arquivos estritamente abaixo de **< 100 KB**.

O modo padrão é o quadro estático de status descrito acima. Escolher outra predefinição alterna para o **modo gif**, que compõe um GIF animado em loop (personagem no meio, com cabeçalho e rodapé de status mantidos) reproduzido localmente pelo dispositivo — um upload por estado, sem tráfego por quadro. O estado ainda é sinalizado pela barra de destaque superior + cor de fundo.

| Predefinição | O que mostra |
|---|---|
| `default` | Quadro estático (o comportamento original) |
| `hosts` | Um GIF de personagem por host, embutido, no meio; cabeçalho + rodapé mantidos |
| `custom` | Seus próprios GIFs, por host e/ou por estado (ver esquema) |

Escolha uma predefinição com o flag CLI `--preset` (persiste em `config.json`, como `--ip`):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` vem com espaços reservados neutros em `assets/gif/`. Substitua um soltando um `<host>.gif` em `~/.agent-glance/gifs/hosts/` (ex.: `claude-code.gif`, `codex.gif`, `antigravity.gif`, `hermes.gif`, `agent.gif`) — o arquivo do usuário prevalece sobre o embutido.

### Especificações ideais de GIF

| Parâmetro | Layout `frame` | Layout `fullscreen` |
|---|---|---|
| **Resolução ideal** | **224 × 116 px** (~1.93:1) ou **116 × 116 px** (1:1) | **240 × 240 px** (quadrado 1:1) |
| **Alvo de composição** | Ajusta-se dentro de `MIDDLE_BOX = (8, 46, 224, 116)` | Cobre toda a tela de 1.54" do SmallTV |
| **Tamanho de arquivo recomendado** | **< 100 KB** (Máximo estrito < 300 KB para evitar falhas de RAM/OOM e reinicializações no ESP8266) |
| **Contagem de quadros** | **12 – 16 quadros** (o renderizador reduz quadros excedentes para `_MAX_FRAMES = 16`) |
| **Atraso de quadro** | **80ms – 150ms** por quadro (loop de 1.2s – 2.0s) |
| **Paleta de cores** | **64 – 128 cores** (otimiza a velocidade de renderização e desgaste da Flash) |

**Reduzir um GIF de origem para a especificação** (exportações brutas facilmente passam de vários MB): amostre quadros uniformemente por todo o clipe e depois recodifique com um loop curto para que toda a amplitude de movimento sobreviva mesmo com a velocidade de reprodução comprimida.

1 — amostre ~14 quadros uniformemente da origem, recortados/escalados conforme o layout:

```bash
# layout frame: encaixado com letterbox em MIDDLE_BOX, então só reduzir a escala (sem necessidade de recorte)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# layout fullscreen: esticado para preencher 240x240, então recorte para quadrado antes ou vai distorcer
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = número de quadros da origem ÷ 14 (arredondado para baixo) — use ffprobe na origem (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`) para obtê-lo.

2 — recodifique os quadros amostrados com um loop curto (10fps = 100ms/quadro ≈ 1.4s de loop para 14 quadros) e uma paleta pequena:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Ainda acima de 300 KB? Reduza `max_colors` para 32 (tente também `dither=none`) antes de cortar a contagem de quadros — é isso que realmente encarece o loop.


`custom` lê `display.gifs` do `config.json`. Cada entrada de host é uma string de caminho (um GIF para todos os estados) ou um mapa por estado; `"default"` é o fallback. Qualquer entrada também pode ser `{"path": ..., "layout": "fullscreen"}` para ir tela cheia somente nessa:

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

Ordem de resolução por push: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → espaço reservado embutido de hosts. Um GIF ausente ou ilegível nunca apaga a tela — recai para o quadro estático.

## Comandos

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Integração completa — descobre o dispositivo, verifica o firmware, salva o IP, faz backup, assume o controle |
| `/agent-glance:status` | Verificação de saúde — acessibilidade, tema ativo, hooks duplicados, log de erros |
| `/agent-glance:test` | Envia um quadro (ou percorre os três) para verificar a renderização |
| `/agent-glance:theme` | Espiar as telas nativas do dispositivo — clima, previsão, relógios (Ultra; o monitor volta na próxima atividade) |
| `/agent-glance:restore` | Devolve o dispositivo ao seu relógio e fotos originais |

Algumas opções são **apenas flags CLI** (sem comando de barra) — persistem em `~/.agent-glance/config.json`, espelhando `--ip`:

| Flag | O que faz |
|---|---|
| `--ip <IP>` | salva o IP do dispositivo |
| `--preset default\|hosts\|custom` | alterna o modo de exibição (ver [Modo GIF](#modo-gif-e-predefinições)) |
| `--layout frame\|fullscreen` | layout do modo gif (`frame` mantém cabeçalho+rodapé; `fullscreen` é somente o GIF) |
| `--test [state] [subtitle]` | envia um quadro; respeita a predefinição atual, então também pré-visualiza o modo gif |

## Como funciona

Esse firmware **não tem API de texto**, então não há nada para "imprimir". Em vez disso, o script renderiza um GIF de 240×240 com Pillow e o envia para o álbum de fotos do dispositivo, tornando essa imagem a única foto habilitada e o Photo o único tema habilitado — assim o quadro fica fixo em vez de girar para outro tema. O decodificador de GIF do firmware também reproduz GIFs **animados**, então no modo gif o script compõe um GIF multiquadro e o dispositivo o reproduz em loop localmente — um upload por estado, sem tráfego por quadro.

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

## Referência da API do dispositivo (SmallTV Ultra, firmware de fábrica)

Temas: 1 Relógio do tempo de hoje · 2 Previsão · **3 Álbum de fotos** · 4–6 Estilos de relógio · 7 Relógio simples.

| Action | Endpoint |
|---|---|
| enviar imagem | `POST /doUpload?dir=/image/` (campo multipart `image`; reenviar com o mesmo nome sobrescreve) |
| fixar no ecrã | `GET /set?img=/image/<f>` (codificado como URL; requer o tema 3) |
| mudar de tema | `GET /set?theme=<n>` |
| flags de temas | `GET /set?theme_list=0,0,1,0,0,0,0&sw_en=0&theme_interval=10` |
| eliminar ficheiro | `GET /delete?file=/image/<f>` |
| ler estado | `GET /app.json` (`theme`), `/theme_list.json`, `/filelist?dir=/image/`, `/space.json` |

Armadilhas encontradas ao sondar um dispositivo real:

- A imagem exibida fica *fixada* por `/set?img=` — os outros ficheiros do álbum ficam mas nunca alternam (sem flags por foto como no SD_RU; o setup não os toca).
- Os GIFs animados são descodificados e repetidos localmente; todo o sistema de 3 MB é partilhado com os recursos de relógio/tempo, por isso mantenham os GIFs pequenos (~1 MB livre de fábrica).
- `/set?img=` e `/set?theme=` devolvem o literal `OK`, não JSON.
- ⚠️ mesma postura de confiança do SD_RU: todos os endpoints sem autenticação na LAN.

## Limitações

- **Os 7 temas do dispositivo não podem exibir uma sessão cada um.** Somente o tema Photo renderiza conteúdo personalizado; os outros seis são interfaces fixas de relógio/clima. Alternar entre várias sessões exigiria várias imagens no álbum — isso não está implementado.
- As métricas vêm do formato de transcrição do Claude Code. No Codex/agy as cores de estado continuam funcionando, mas os campos de modelo/tokens podem ficar em branco.
- O estado (`config.json`, `device_backup.json`) fica em `~/.agent-glance/`, não no diretório do plugin, portanto não é apagado em atualizações do plugin.

## Licença

[MIT](../../../LICENSE)
