# Automation BDD — Agente do Projeto

Diretório raiz: raiz deste repositório (`automation-bdd/`)

Você é o agente deste projeto de automação mobile BDD. Quando a usuária pedir qualquer coisa relacionada ao projeto, execute imediatamente usando as ferramentas disponíveis — sem pedir confirmação para ações normais.

Responda sempre em **português**.

---

## 1. GRAVAÇÃO DE CENÁRIOS

Registra cenários .feature conversacionalmente via `utils/recorder.py`.

### Comandos

```bash
cd <raiz-do-projeto>

# Iniciar
python -m utils.recorder start "nome_do_cenario"

# Adicionar passo
python -m utils.recorder step "Given" "descrição"
python -m utils.recorder step "When"  "descrição"
python -m utils.recorder step "Then"  "descrição"
python -m utils.recorder step "And"   "descrição"

# Finalizar (salva em features/automation_scripts/<nome>.feature)
python -m utils.recorder stop

# Ver o que foi gravado
python -m utils.recorder status
```

### Mapeamento de linguagem → keyword

| O que a usuária diz | Keyword |
|---|---|
| "dado que...", "começa com...", "estou com..." | `Given` |
| "abrir", "tocar", "clicar", "pesquisar", "digitar", "navegar" | `When` |
| "verificar", "checar", "deve aparecer", "valido" | `Then` |
| "e também", "e depois", "e ainda" | `And` |

Se descrever várias ações de uma vez, adicione **todos os passos em sequência** antes de responder.

---

## 2. EXECUÇÃO DE TESTES

### Rodar tudo

```bash
cd <raiz-do-projeto>
./run.sh
```

### Feature específica

```bash
./run.sh features/pesquisar_batata_da_terra.feature
./run.sh features/automation_scripts/alterando_ajustes.feature
```

### Filtrar por tag

```bash
./run.sh --tags @smoke
./run.sh --tags @regressao
```

### Forçar plataforma

```bash
./run.sh --platform ios
./run.sh --platform android
```

### Cenário específico

```bash
behave features/pesquisar_batata_da_terra.feature --name "Nome do Cenário"
```

### Dry-run (valida sem executar)

```bash
behave --dry-run features/
```

---

## 3. EXECUÇÃO PARALELA (iOS + Android simultâneo)

```bash
cd <raiz-do-projeto>

# Todas as features nos dois dispositivos
./run-parallel.sh

# Feature específica
./run-parallel.sh features/pesquisar_batata_da_terra.feature

# Só iOS
./run-parallel.sh features/ --platform ios

# Só Android
./run-parallel.sh features/ --platform android

# Com filtro de tag
./run-parallel.sh features/ --tags @smoke
```

Logs em tempo real com prefixo `[iOS]` e `[Android]`. Resultado final exibe ✓/✗ por plataforma e envia notificação macOS.

---

## 4. CRIAR NOVOS STEPS

Steps existentes ficam em `features/steps/`. Os arquivos são:
- `common_steps.py` — navegação genérica, home, voltar, scroll, tap, digitar, screenshot, apps
- `safari_steps.py` — Safari/Chrome: abrir, fechar, pesquisar, navegar para URL
- `settings_steps.py` — Ajustes/Settings: abrir, fechar, aguardar elemento

### Regras para criar steps

1. **Leia o arquivo correspondente** antes de editar para não duplicar
2. Adicione no arquivo mais adequado ao contexto
3. Siga o padrão existente: use `@step(u'...')` com variações naturais
4. Para ações com argumento (label, texto, URL), use `{label}`, `{texto}`, `{url}`
5. Acesse o device via `context.session` (instância de `AppiumSession`)

### Métodos disponíveis em `context.session`

```python
# Apps
context.session.launch_app("com.apple.mobilesafari")
context.session.terminate_app("com.apple.Preferences")
context.session.open_url("https://...")
context.session.search("termo de busca")

# Navegação
context.session.home()
context.session.back()

# Interação
context.session.tap_by_label("Nome do Elemento")
context.session.tap_switch("Nome do Toggle")
context.session.tap_by_coords(x, y)
context.session.type_text("texto")

# Scroll
context.session.scroll_down()
context.session.scroll_up()
context.session.scroll_left()
context.session.scroll_right()
context.session.swipe(x1, y1, x2, y2, duration_ms=300)

# Espera e verificação
context.session.wait_for_element("label", timeout=15)  # retorna bool
context.session.get_page_source()  # XML de acessibilidade

# Screenshot
context.session.screenshot("/caminho/arquivo.png")

# Plataforma atual
context.platform  # "ios" ou "android"
```

### Exemplo — novo step em `safari_steps.py`

```python
@step(u'abro o instagram')
@step(u'inicio o instagram')
def step_abrir_instagram(context):
    context.session.launch_app("com.burbn.instagram")
    time.sleep(2)
```

### Criando um step file novo (novo domínio de app)

```python
"""
nome_steps.py — Steps para [descrição do app/contexto].
"""
import time
from behave import given, when, then, step

@step(u'...')
def step_nome(context):
    ...
```

---

## 5. CRIAR NOVAS FEATURES

Features ficam em `features/` (manuais) ou `features/automation_scripts/` (geradas pelo recorder).

### Estrutura padrão

```gherkin
Feature: Nome da Feature

  Scenario: Nome do Cenário
    Given pré-condição
    When ação
    Then verificação
```

### Com tags

```gherkin
@smoke @ios
Feature: Nome

  @regressao
  Scenario: Cenário específico
    Given ...
```

### Com múltiplos cenários

```gherkin
Feature: Pesquisa no Navegador

  Scenario: Pesquisar por texto simples
    Given abro o safari
    When pesquiso batata da terra
    Then tiro um screenshot

  Scenario: Navegar para URL específica
    Given abro o safari
    When navego para a url google.com
    Then tiro um screenshot
```

---

## 6. STEPS DISPONÍVEIS (referência rápida)

### Navegação geral (`common_steps.py`)

```
volto / volta / voltar / clico em voltar
tela inicial / home / ir para home
aguardo N segundo(s) / espero N segundo(s)
tiro um screenshot / capturo a tela
clico em {label} / toco em {label} / pressiono {label}
scroll para baixo / cima / esquerda / direita
digito {texto} / escrevo {texto}
abro o navegador / inicio o navegador
abro o app {bundle} / fecho o app {bundle}
```

### Safari / Chrome (`safari_steps.py`)

```
abro o safari / inicio o safari
fecho o safari
pesquiso {query} / busco {query} / procuro {query}
pesquize {query}
abro a url {url} / navego para a url {url}
```

### Ajustes (`settings_steps.py`)

```
abro os ajustes / acesso os ajustes / abrir ajustes
fecho os ajustes
clicar em {label} / clico em {label}
clicar no seletor de {label} / ativo o seletor de {label}
aguardo o elemento {label} / espero aparecer {label}
```

---

## 7. BUNDLE IDs MAPEADOS (iOS → Android automático)

| iOS | Android |
|---|---|
| `com.apple.mobilesafari` | `com.android.chrome` |
| `com.apple.Preferences` | `com.android.settings` |
| `com.apple.camera` | `com.android.camera2` |
| `com.apple.MobileSMS` | `com.google.android.apps.messaging` |
| `com.apple.Maps` | `com.google.android.apps.maps` |
| `com.apple.mobilenotes` | `com.google.android.keep` |

---

## 8. COMPORTAMENTO DE TOGGLE SWITCHES NO iOS

### Hierarquia real (descoberta via page_source)

No iOS, um toggle switch na tela tem esta estrutura no XML de acessibilidade:

```
XCUIElementTypeSwitch [label="Grade", accessible=true, width=TOTAL]
  ├─ XCUIElementTypeButton [label="Grade", accessible=false]  ← texto/label
  └─ XCUIElementTypeSwitch [accessible=false, width=63]       ← knob (botão físico)
```

- O switch **externo** (acessível) cobre a largura total da célula (label + knob juntos).
- `el.click()` no externo toca o **centro** → cai no texto, não no knob → não alterna.
- O knob é um **filho** do switch externo, não um irmão.

### Estratégia que funciona

`//XCUIElementTypeButton[@label="Grade"]/following-sibling::XCUIElementTypeSwitch`

Mesmo com o knob sendo `accessible=false`, o Appium **consegue** encontrá-lo via
travessia XPath relativa a partir de um elemento acessível (`following-sibling`).
O `find_element` direto no knob falha; a navegação relativa funciona.

Ordem de tentativas em `tap_switch` / `live_runner`:
1. `button[@label] → following-sibling::Switch` ← **funciona, confirmado**
2. `Switch[@label] → child Switch` ← fallback
3. Coordenada: `rect["x"] + rect["width"] - 32` (32px da borda direita) ← fallback final

### Step correspondente

```
clicar no seletor de {label}
clico no seletor de {label}
ativo o seletor de {label}
```

---

## 10. SCREENSHOTS E ACESSIBILIDADE

### Tirar screenshot manualmente

```bash
# Via behave step (dentro de um cenário):
# "tiro um screenshot"

# Via Python direto (fora de teste):
python3 -c "
from driver.appium_driver import AppiumSession
from utils.screenshot import take_screenshot
s = AppiumSession()
s.start()
take_screenshot(s, 'meu_screenshot')
s.stop()
"
```

Screenshots são salvos em `automation_scripts/screenshots/` com timestamp e plataforma no nome.

### Inspecionar árvore de acessibilidade

```python
from utils.accessibility import parse_tree, print_tree, find_by_label

tree = parse_tree(context.session.get_page_source(), context.platform)
print_tree(tree)  # imprime estrutura completa
el = find_by_label(tree, "Buscar")  # encontra elemento por label
print(el.center_x, el.center_y)     # coordenadas do centro
```

---

## 11. VERIFICAR DISPOSITIVOS

```bash
# iOS — simuladores disponíveis
xcrun simctl list devices

# iOS — simuladores ativos (Booted)
xcrun simctl list devices booted

# Android — devices conectados
adb devices

# Appium — verificar se está rodando
curl -s http://localhost:4723/status | python3 -m json.tool
```

---

## 12. ESTRUTURA DE ARQUIVOS

```
automation-bdd/
├── features/
│   ├── environment.py              ← hooks before/after (Appium lifecycle)
│   ├── pesquisar_batata_da_terra.feature
│   ├── automation_scripts/         ← features geradas pelo recorder
│   │   └── alterando_ajustes.feature
│   └── steps/
│       ├── common_steps.py         ← steps genéricos (nav, scroll, tap...)
│       ├── safari_steps.py         ← steps de navegador
│       └── settings_steps.py       ← steps de ajustes/settings
├── driver/
│   ├── appium_driver.py            ← AppiumSession (todas as interações)
│   └── device_manager.py           ← detecção de plataforma, boot de device
├── utils/
│   ├── recorder.py                 ← gravação de cenários Gherkin
│   ├── screenshot.py               ← captura de tela com timestamp
│   └── accessibility.py            ← parse da árvore XML do Appium
├── automation_scripts/
│   └── screenshots/                ← screenshots de execução
├── run.sh                          ← execução simples
├── run-parallel.sh                 ← execução iOS + Android simultânea
├── behave.ini                      ← configuração do Behave
└── requirements.txt
```
