# automation-bdd

Automação de testes mobile com **Appium 2**, **Python** e **Behave (BDD/Gherkin)**.

Suporta iOS (XCUITest) e Android (UiAutomator2) com detecção automática de plataforma.
Possui agente conversacional integrado ao Claude Code para gravação de cenários em linguagem natural.

---

## Arquitetura

```
automation-bdd/
├── features/
│   ├── environment.py              # Hooks Behave: lifecycle da sessão Appium
│   ├── *.feature                   # Cenários escritos manualmente
│   ├── automation_scripts/         # Cenários gerados pelo recorder/agente
│   └── steps/
│       ├── common_steps.py         # Steps genéricos: nav, scroll, tap, digitar
│       ├── safari_steps.py         # Steps de navegador (Safari/Chrome)
│       └── settings_steps.py       # Steps de Ajustes/Settings
├── driver/
│   ├── appium_driver.py            # AppiumSession — todas as interações com o device
│   └── device_manager.py           # Detecção de plataforma, boot de simulador/emulador
├── utils/
│   ├── recorder.py                 # Gravação de cenários Gherkin via CLI ou agente
│   ├── live_runner.py              # Daemon de execução ao vivo durante gravação
│   ├── screenshot.py               # Captura de tela com timestamp e plataforma
│   └── accessibility.py            # Parse da árvore XML de acessibilidade do Appium
├── automation_scripts/
│   └── screenshots/                # Evidências de execução (gerado automaticamente)
├── alfred                          # CLI principal — ponto de entrada de tudo
├── run.sh                          # Execução simples (chamado pelo alfred)
├── run-parallel.sh                 # Execução paralela (chamado pelo alfred)
├── behave.ini                      # Configuração do Behave
├── requirements.txt
└── CLAUDE.md                       # Instruções do agente Claude Code
```

---

## Pré-requisitos

| Dependência | Versão mínima | Para |
|---|---|---|
| Python | 3.11+ | Runtime |
| Appium | 2.x | Servidor de automação |
| Appium XCUITest driver | 7.x | iOS |
| Appium UiAutomator2 driver | 3.x | Android |
| Xcode + Simulador | 15+ | iOS local |
| Android Studio + AVD | — | Android local |

Instalar dependências Python:

```bash
pip install -r requirements.txt
```

Instalar Appium e drivers:

```bash
npm install -g appium
appium driver install xcuitest
appium driver install uiautomator2
```

---

## Alfred — CLI principal

O `alfred` é o ponto de entrada de tudo no projeto. Sem precisar decorar comandos do behave, run.sh ou recorder.

```bash
./alfred                           # menu de ajuda completo
```

### Referência de comandos

| Comando | O que faz |
|---|---|
| `./alfred gravar <nome>` | Inicia gravação de um cenário |
| `./alfred passo <keyword> <desc>` | Adiciona passo (Given/When/Then/And) |
| `./alfred status` | Mostra passos gravados até agora |
| `./alfred parar` | Finaliza e salva o `.feature` |
| `./alfred rodar` | Roda todas as features |
| `./alfred rodar <feature>` | Roda uma feature específica |
| `./alfred rodar --tags @smoke` | Filtra por tag |
| `./alfred rodar --platform ios` | Força plataforma iOS ou Android |
| `./alfred paralelo` | Roda iOS + Android em paralelo |
| `./alfred live iniciar` | Sobe daemon Appium em background |
| `./alfred live parar` | Para o daemon |
| `./alfred live status` | Verifica se o daemon está rodando |
| `./alfred devices` | Lista simuladores iOS e devices Android |
| `./alfred appium` | Verifica se o Appium está rodando |
| `./alfred screenshot` | Tira screenshot avulso do device |

---

## Como usar

### 1. Iniciar o Appium

```bash
appium
```

### 2. Verificar dispositivos

```bash
./alfred devices    # lista simuladores iOS e devices Android ativos
./alfred appium     # confirma que o servidor está no ar
```

### 3. Rodar testes

```bash
./alfred rodar                                                        # todas as features
./alfred rodar features/automation_scripts/editando_ajustes.feature  # feature específica
./alfred rodar --tags @smoke                                          # filtro por tag
./alfred rodar --platform ios                                         # força plataforma
./alfred paralelo                                                     # iOS + Android ao mesmo tempo
```

Logs em tempo real com prefixo `[iOS]` e `[Android]`. Resultado final exibe ✓/✗ por plataforma.

---

## Gravação de cenários

### Via Alfred

```bash
./alfred live iniciar                          # sobe sessão Appium em background
./alfred gravar editando_ajustes               # começa a gravar
./alfred passo Given "abro os ajustes"
./alfred passo When  "clicar em câmera"
./alfred passo When  "clicar no seletor de Grade"
./alfred passo Then  "volto para home"
./alfred parar                                 # salva em features/automation_scripts/
```

### Via agente (Claude Code)

Com o projeto aberto no Claude Code, descreva os passos em linguagem natural:

> "grava um cenário que abre o safari, pesquisa por 'batata da terra' e tira screenshot"

O agente converte para Gherkin, grava os steps e — com o live runner ativo — executa cada passo em tempo real no device.

#### Live Runner

O live runner mantém uma sessão Appium ativa em background para execução ao vivo durante a gravação.

```bash
./alfred live iniciar   # inicia o daemon
./alfred live status    # verifica se está rodando
./alfred live parar     # encerra o daemon
```

Comunicação interna via arquivos em `/tmp/`:

| Arquivo | Função |
|---|---|
| `/tmp/bdd_live_cmd` | Step a executar (escrito pelo agente) |
| `/tmp/bdd_live_result` | Resultado: `ok` ou `erro: ...` |
| `/tmp/bdd_live_ready` | Existe quando a sessão está pronta |
| `/tmp/bdd_live_pid` | PID do daemon |

---

## Steps disponíveis

### Navegação geral

```gherkin
Given volto para home
When  clico em {label}
When  toco em {label}
When  scroll para baixo
When  scroll para cima
When  digito {texto}
When  aguardo 2 segundos
Then  tiro um screenshot
```

### Safari / Chrome

```gherkin
Given abro o safari
When  pesquiso {query}
When  navego para a url {url}
Then  fecho o safari
```

### Ajustes / Settings

```gherkin
Given abro os ajustes
When  clicar em {label}
When  clicar no seletor de {label}
When  aguardo o elemento {label}
Then  fecho os ajustes
```

---

## Evidências automáticas

Ao final de cada cenário que passa, um screenshot é salvo automaticamente em:

```
automation_scripts/screenshots/evidencia_<NomeCenario>_<plataforma>_<timestamp>.png
```

Em caso de falha:

```
automation_scripts/screenshots/FALHA_<NomeCenario>_<timestamp>.png
```

---

## Comportamento de toggle switches no iOS

No iOS, um toggle switch tem a seguinte hierarquia no XML de acessibilidade:

```
XCUIElementTypeSwitch [label="Grade", accessible=true, width=total]
  ├─ XCUIElementTypeButton [label="Grade", accessible=false]  ← texto
  └─ XCUIElementTypeSwitch [accessible=false, width=63]       ← knob
```

O `tap_switch` usa três estratégias em cascata:

1. `//XCUIElementTypeButton[@label="X"]/following-sibling::XCUIElementTypeSwitch` — **principal** (funciona mesmo com `accessible=false` via travessia XPath relativa)
2. `//XCUIElementTypeSwitch[@label="X"]/XCUIElementTypeSwitch` — child do outer switch
3. Coordenada: `rect["x"] + rect["width"] - 32` — fallback por posição do knob

---

## Bundle IDs mapeados (iOS → Android automático)

| iOS | Android |
|---|---|
| `com.apple.mobilesafari` | `com.android.chrome` |
| `com.apple.Preferences` | `com.android.settings` |
| `com.apple.camera` | `com.android.camera2` |
| `com.apple.MobileSMS` | `com.google.android.apps.messaging` |
| `com.apple.Maps` | `com.google.android.apps.maps` |
| `com.apple.mobilenotes` | `com.google.android.keep` |

---

## Criar novos steps

Adicione em `features/steps/` no arquivo mais adequado ao contexto:

```python
from behave import step
import time

@step(u'abro o instagram')
@step(u'inicio o instagram')
def step_abrir_instagram(context):
    context.session.launch_app("com.burbn.instagram")
    time.sleep(2)
```

Métodos disponíveis em `context.session` (instância de `AppiumSession`):

```python
context.session.launch_app(bundle_id)
context.session.terminate_app(bundle_id)
context.session.open_url(url)
context.session.search(query)
context.session.home()
context.session.back()
context.session.tap_by_label(label)
context.session.tap_switch(label)       # toggle switch com 3 estratégias
context.session.tap_by_coords(x, y)
context.session.type_text(texto)
context.session.scroll_down()
context.session.scroll_up()
context.session.swipe(x1, y1, x2, y2)
context.session.wait_for_element(label, timeout=15)
context.session.get_page_source()       # XML de acessibilidade
context.session.screenshot(path)
context.platform                        # "ios" ou "android"
```
