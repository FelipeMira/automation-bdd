"""
safari_steps.py — Steps para o Safari (iOS) e Chrome (Android).

Cobre: abrir/fechar navegador, pesquisar, navegar para URL.
"""

import time

from behave import given, when, then, step


# ─── Abrir Safari ─────────────────────────────────────────────────────────────

@step(u'abro o safari')
@step(u'abrir o safari')
@step(u'inicio o safari')
@step(u'abre o safari')
def step_abrir_safari(context):
    context.session.launch_app("com.apple.mobilesafari")
    time.sleep(1.5)


# ─── Fechar Safari ────────────────────────────────────────────────────────────

@step(u'fecho o safari')
@step(u'fechar o safari')
@step(u'encerro o safari')
def step_fechar_safari(context):
    context.session.terminate_app("com.apple.mobilesafari")


# ─── Pesquisar ────────────────────────────────────────────────────────────────
# Nota: {query} captura tudo após o verbo, inclusive "no navegador" se presente.
# A função normaliza removendo esse sufixo.

def _normalize_query(query: str) -> str:
    for suffix in (" no navegador", " no browser", " no safari"):
        if query.lower().endswith(suffix):
            query = query[: -len(suffix)]
    return query.strip()


@step(u'pesquiso {query}')
@step(u'pesquisar {query}')
@step(u'busco {query}')
@step(u'buscar {query}')
@step(u'procuro {query}')
@step(u'search {query}')
def step_pesquisar(context, query):
    context.session.search(_normalize_query(query))


@step(u'pesquize {query}')
def step_pesquize(context, query):
    context.session.search(_normalize_query(query))


# ─── Navegar para URL ─────────────────────────────────────────────────────────

@step(u'abro a url {url}')
@step(u'navego para a url {url}')
def step_navegar_url(context, url):
    if not url.startswith("http"):
        url = "https://" + url
    context.session.open_url(url)
