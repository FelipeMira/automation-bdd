"""
common_steps.py — Steps genéricos de navegação e controle.

Cobre: voltar, home, aguardar, screenshot, tap, scroll, digitar, abrir navegador.
"""

import time

from behave import given, when, then, step
from selenium.common.exceptions import NoSuchElementException

from utils.screenshot import take_screenshot

# ─── Voltar ───────────────────────────────────────────────────────────────────

@step(u'volto')
@step(u'volta')
@step(u'voltar')
@step(u'clico em voltar')
@step(u'boto voltar')
@step(u'ir para trás')
def step_voltar(context):
    context.session.back()


# ─── Home ─────────────────────────────────────────────────────────────────────

@step(u'tela inicial')
@step(u'home')
@step(u'ir para home')
@step(u'página inicial')
@step(u'acesse home')
@step(u'acesso home')
@step(u'volto para home')
@step(u'voltar para home')
def step_home(context):
    context.session.home()


# ─── Aguardar ─────────────────────────────────────────────────────────────────

@step(u'aguardo {segundos:d} segundo')
@step(u'aguardo {segundos:d} segundos')
@step(u'espero {segundos:d} segundo')
@step(u'espero {segundos:d} segundos')
@step(u'wait {segundos:d}')
def step_aguardar(context, segundos):
    time.sleep(segundos)


@step(u'aguardo')
@step(u'espero')
def step_aguardar_padrao(context):
    time.sleep(2)


# ─── Screenshot ───────────────────────────────────────────────────────────────

@step(u'tiro um screenshot')
@step(u'capturo a tela')
@step(u'tiro screenshot')
@step(u'salvo a tela')
def step_screenshot(context):
    take_screenshot(context.session, "screenshot")


@step(u'tiro um screenshot de {label}')
@step(u'capturo {label}')
def step_screenshot_label(context, label):
    take_screenshot(context.session, label)


# ─── Tap genérico ─────────────────────────────────────────────────────────────

@step(u'clico em {label}')
@step(u'toco em {label}')
@step(u'toco no {label}')
@step(u'toco na {label}')
@step(u'pressiono {label}')
@step(u'tap em {label}')
def step_tap(context, label):
    context.session.tap_by_label(label)


# ─── Scroll ───────────────────────────────────────────────────────────────────

@step(u'scroll para baixo')
@step(u'rolo para baixo')
@step(u'deslizo para baixo')
def step_scroll_baixo(context):
    context.session.scroll_down()


@step(u'scroll para cima')
@step(u'rolo para cima')
@step(u'deslizo para cima')
def step_scroll_cima(context):
    context.session.scroll_up()


@step(u'scroll para esquerda')
@step(u'deslizo para esquerda')
def step_scroll_esquerda(context):
    context.session.scroll_left()


@step(u'scroll para direita')
@step(u'deslizo para direita')
def step_scroll_direita(context):
    context.session.scroll_right()


# ─── Digitar ──────────────────────────────────────────────────────────────────

@step(u'digito {texto}')
@step(u'escrevo {texto}')
@step(u'insiro {texto}')
@step(u'tipo {texto}')
def step_digitar(context, texto):
    context.session.type_text(texto)


# ─── Abrir navegador ──────────────────────────────────────────────────────────

@step(u'abro o navegador')
@step(u'abrir o navegador')
@step(u'inicio o navegador')
@step(u'acesso o navegador')
def step_abrir_navegador(context):
    if context.platform == "android":
        context.session.launch_app("com.android.chrome")
    else:
        context.session.launch_app("com.apple.mobilesafari")
    time.sleep(2)


# ─── App genérico ─────────────────────────────────────────────────────────────

@step(u'abro o app {bundle}')
@step(u'inicio o app {bundle}')
def step_abrir_app(context, bundle):
    context.session.launch_app(bundle)
    time.sleep(1.5)


@step(u'fecho o app {bundle}')
@step(u'encerro o app {bundle}')
def step_fechar_app(context, bundle):
    context.session.terminate_app(bundle)
