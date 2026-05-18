# Gerado em: 17/05/2026 — portado de automation_scripts/pesquisar_batata_da_terra.sh
Feature: Pesquisar Batata Da Terra

  Scenario: Pesquisar batata da terra no navegador
    Given abro o safari
    When pesquize batata da terra no navegador
    Then tiro um screenshot
