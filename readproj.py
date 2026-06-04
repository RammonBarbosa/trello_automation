import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import requests
from dotenv import load_dotenv


caminho_env = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(caminho_env)

API_KEY = os.getenv("API_KEY")
TOKEN = os.getenv("TOKEN")

# --- CONFIGURACAO DE LISTAS ---
LISTA_PROJETO_SOLICITACOES = "6669a662923d4751850ae26a"
LISTA_FINALIZADOS_PROJETOS = "66a3cd4cf460377406141493"

TRELLO_API = "https://api.trello.com/1"
TIMEOUT = 20
MAX_TENTATIVAS = 3
INTERVALO_ENTRE_REQUISICOES = 0.2


@dataclass
class ResultadoProjeto:
    nome: str
    status: str
    motivo: str
    projeto_anexado: str | None = None
    detalhes: list[str] = field(default_factory=list)


def validar_configuracao() -> None:
    if not API_KEY or not TOKEN:
        raise RuntimeError("API_KEY ou TOKEN nao foram carregados. Confira o arquivo .env.")


def extrair_shortlink_trello(url: str | None) -> str | None:
    if not url:
        return None

    match = re.search(r"trello\.com/c/([^/?#]+)", url, flags=re.IGNORECASE)
    if not match:
        return None

    return match.group(1)


def requisicao_trello(metodo: str, caminho: str, **params: Any) -> requests.Response:
    url = f"{TRELLO_API}{caminho}"
    params = {"key": API_KEY, "token": TOKEN, **params}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            response = requests.request(metodo, url, params=params, timeout=TIMEOUT)
        except requests.RequestException as erro:
            if tentativa == MAX_TENTATIVAS:
                raise RuntimeError(f"Falha de conexao com o Trello: {erro}") from erro

            print(f"Falha de conexao. Tentando novamente ({tentativa}/{MAX_TENTATIVAS})...")
            time.sleep(2 * tentativa)
            continue

        if response.status_code != 429:
            time.sleep(INTERVALO_ENTRE_REQUISICOES)
            return response

        espera = int(response.headers.get("Retry-After", "10"))
        print(f"Rate limit do Trello. Aguardando {espera}s antes de tentar novamente...")
        time.sleep(espera)

    return response


def buscar_cartoes_lista(id_lista: str) -> list[dict[str, Any]]:
    response = requisicao_trello(
        "GET",
        f"/lists/{id_lista}/cards",
        attachments="true",
        fields="id,name,idList,shortLink,url",
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Erro ao acessar a lista no Trello. "
            f"Lista: {id_lista}. Status: {response.status_code}. Resposta: {response.text}"
        )

    return response.json()


def buscar_cartao(shortlink_ou_id: str) -> tuple[dict[str, Any] | None, requests.Response]:
    response = requisicao_trello(
        "GET",
        f"/cards/{shortlink_ou_id}",
        fields="id,name,idList,idBoard,closed,shortLink,url",
    )

    if response.status_code != 200:
        return None, response

    return response.json(), response


def shortlinks_dos_anexos(cartao: dict[str, Any]) -> list[str]:
    shortlinks: list[str] = []
    vistos = set()

    for anexo in cartao.get("attachments", []):
        shortlink = extrair_shortlink_trello(anexo.get("url"))
        if shortlink and shortlink not in vistos:
            shortlinks.append(shortlink)
            vistos.add(shortlink)

    return shortlinks


def analisar_cartao_para_execucao(cartao: dict[str, Any]) -> ResultadoProjeto:
    nome_cartao = cartao.get("name", "Sem nome")
    shortlinks = shortlinks_dos_anexos(cartao)

    if not shortlinks:
        return ResultadoProjeto(
            nome=nome_cartao,
            status="SEM_ANEXO",
            motivo="cartao sem anexo Trello de projeto",
        )

    erros: list[str] = []
    anexos_lidos: list[str] = []

    for shortlink in shortlinks:
        projeto, response = buscar_cartao(shortlink)

        if projeto is None:
            erros.append(
                f"erro {response.status_code} ao ler anexo {shortlink}: {response.text}"
            )
            continue

        nome_projeto = projeto.get("name", "Projeto sem nome")
        id_lista = projeto.get("idList")
        anexos_lidos.append(f"{nome_projeto} esta na lista {id_lista}")

        if id_lista == LISTA_FINALIZADOS_PROJETOS:
            return ResultadoProjeto(
                nome=nome_cartao,
                status="PRONTO",
                motivo="existe projeto anexado na lista Finalizados",
                projeto_anexado=nome_projeto,
                detalhes=anexos_lidos,
            )

    if anexos_lidos:
        return ResultadoProjeto(
            nome=nome_cartao,
            status="NAO_PRONTO",
            motivo="nenhum projeto anexado esta na lista Finalizados",
            detalhes=anexos_lidos,
        )

    return ResultadoProjeto(
        nome=nome_cartao,
        status="ERRO",
        motivo="; ".join(erros),
    )


def imprimir_resultado(resultado: ResultadoProjeto) -> None:
    rotulos = {
        "PRONTO": "[PRONTO PARA EXECUCAO]",
        "NAO_PRONTO": "[NAO PRONTO]",
        "SEM_ANEXO": "[SEM ANEXO TRELLO]",
        "ERRO": "[ERRO DE LEITURA]",
    }

    partes = [f"{rotulos.get(resultado.status, '[STATUS DESCONHECIDO]'):24} {resultado.nome}"]

    if resultado.projeto_anexado:
        partes.append(f"Projeto finalizado: {resultado.projeto_anexado}")

    partes.append(f"Motivo: {resultado.motivo}")

    if resultado.detalhes:
        partes.append("Detalhes: " + " | ".join(resultado.detalhes))

    print(" - ".join(partes))


def gerar_relatorio_projetos() -> None:
    validar_configuracao()

    print("Iniciando varredura na lista de Projetos/Solicitacoes...\n")
    cartoes = buscar_cartoes_lista(LISTA_PROJETO_SOLICITACOES)

    totais = {
        "PRONTO": 0,
        "NAO_PRONTO": 0,
        "SEM_ANEXO": 0,
        "ERRO": 0,
    }

    print("DETALHAMENTO DOS CARTOES:")
    print("-" * 100)

    for cartao in cartoes:
        resultado = analisar_cartao_para_execucao(cartao)
        totais[resultado.status] = totais.get(resultado.status, 0) + 1
        imprimir_resultado(resultado)

    total_analisados = len(cartoes)
    total_somado = sum(totais.values())

    print("\n" + "=" * 60)
    print("RELATORIO PREVIO PARA MOVER PARA EXECUCAO")
    print("=" * 60)
    print(f"Total de cartoes na lista:       {total_analisados}")
    print("-" * 60)
    print(f"Prontos para Execucao:           {totais['PRONTO']}")
    print(f"Ainda nao prontos:               {totais['NAO_PRONTO']}")
    print(f"Sem anexo Trello:                {totais['SEM_ANEXO']}")
    print(f"Erros de leitura da API:         {totais['ERRO']}")
    print("-" * 60)
    print(f"Validacao matematica: Soma = {total_somado} (deve ser igual a {total_analisados})")
    print("=" * 60 + "\n")

    print("Observacao: este script apenas gera relatorio. Nenhum cartao e movido.")


if __name__ == "__main__":
    gerar_relatorio_projetos()
