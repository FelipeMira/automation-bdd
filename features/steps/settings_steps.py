"""
settings_steps.py — Steps para Ajustes (iOS) e Settings (Android).

Cobre: abrir/fechar ajustes, aguardar elemento.
Navegação para seções específicas usa os steps de tap do common_steps.py.
"""

import time

from behave import given, when, then, step


# ─── Abrir Ajustes ────────────────────────────────────────────────────────────

@step(u'abro os ajustes')
@step(u'abro as configurações')
@step(u'abrir ajustes')
@step(u'acessar ajustes')
@step(u'acesso os ajustes')
@step(u'acesso as configurações')
@step(u'abre os ajustes')
@step(u'abre as configurações')
def step_abrir_ajustes(context):
    if context.platform == "android":
        context.session.launch_app("com.android.settings")
    else:
        context.session.launch_app("com.apple.Preferences")
    time.sleep(2)

    loaded = (
        context.session.wait_for_element("Geral", timeout=10)
        or context.session.wait_for_element("General", timeout=5)
        or context.session.wait_for_element("Wi-Fi", timeout=5)
        or context.session.wait_for_element("Network", timeout=5)
    )
    if not loaded:
        time.sleep(2)


# ─── Fechar Ajustes ───────────────────────────────────────────────────────────

@step(u'fecho os ajustes')
@step(u'fechar ajustes')
@step(u'encerro os ajustes')
def step_fechar_ajustes(context):
    if context.platform == "android":
        context.session.terminate_app("com.android.settings")
    else:
        context.session.terminate_app("com.apple.Preferences")


# ─── Navegação por label e UID ───────────────────────────────────────────────

@step(u'clicar em {label}')
def step_clicar_em(context, label):
    context.session.tap_by_label(label)
    time.sleep(1)


@step(u'clicar no seletor de {label}')
@step(u'clico no seletor de {label}')
@step(u'ativo o seletor de {label}')
def step_clicar_seletor(context, label):
    # tap_switch busca especificamente XCUIElementTypeSwitch (iOS) / Switch (Android)
    # garantindo que o tap acerta o controle e não a célula pai
    context.session.tap_switch(label)
    time.sleep(0.5)


# ─── Aguardar elemento ────────────────────────────────────────────────────────

@step(u'aguardo o elemento {label}')
@step(u'espero o elemento {label}')
@step(u'espero aparecer {label}')
def step_aguardar_elemento(context, label):
    appeared = context.session.wait_for_element(label, timeout=15)
    assert appeared, f'Elemento "{label}" não apareceu em 15 segundos.'
