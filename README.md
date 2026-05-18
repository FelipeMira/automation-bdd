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
├── run.sh                          # Execução simples (iOS ou Android)
├── run-parallel.sh                 # Execução paralela iOS + Android simultâneo
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

## Como usar

### 1. Iniciar o Appium

```bash
appium
```

### 2. Ter um simulador/emulador ativo

```bash
# iOS — ver simuladores disponíveis
xcrun simctl list devices

# iOS — iniciar um simulador
xcrun simctl boot "<nome-ou-udid>"
open -a Simulator

# Android — verificar emulador
adb devices
```

### 3. Rodar uma feature

```bash
# Todas as features
./run.sh

# Feature específica
./run.sh features/automation_scripts/editando_ajustes.feature

# Com filtro de tag
./run.sh --tags @smoke

# Forçar plataforma
./run.sh --platform ios
./run.sh --platform android
```

### 4. Execução paralela (iOS + Android simultâneo)

```bash
./run-parallel.sh

# Feature específica em paralelo
./run-parallel.sh features/pesquisar_batata_da_terra.feature
```

Logs em tempo real com prefixo `[iOS]` e `[Android]`. Resultado final exibe ✓/✗ por plataforma.

---

## Gravação de cenários

### Via CLI

```bash
python -m utils.recorder start "nome_do_cenario"
python -m utils.recorder step "Given" "abro os ajustes"
python -m utils.recorder step "When"  "clicar em câmera"
python -m utils.recorder step "When"  "clicar no seletor de Grade"
python -m utils.recorder step "Then"  "volto para home"
python -m utils.recorder stop
```

Gera automaticamente `features/automation_scripts/nome_do_cenario.feature`.

### Via agente (Claude Code)

Com o projeto aberto no Claude Code, descreva os passos em linguagem natural:

> "grava um cenário que abre o safari, pesquisa por 'batata da terra' e tira screenshot"

O agente converte para Gherkin, grava os steps e — com o `live_runner` ativo — executa cada passo em tempo real no device.

#### Live Runner (execução ao vivo durante gravação)

```bash
# Iniciar o daemon (mantém sessão Appium ativa)
python -m utils.live_runner

# Parar
python -m utils.live_runner stop
```

Comunicação via arquivos em `/tmp/`:

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
