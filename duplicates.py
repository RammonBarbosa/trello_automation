import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv


caminho_env = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(caminho_env)

API_KEY = os.getenv("API_KEY")
TOKEN = os.getenv("TOKEN")

# Lista "Projetos/Solicitacoes"
LISTA_PROJETO_SOLICITACOES = "6669a662923d4751850ae26a"

TRELLO_API = "https://api.trello.com/1"
TIMEOUT = 20
MAX_TENTATIVAS = 3
INTERVALO_ENTRE_REQUISICOES = 0.2


def validar_configuracao() -> None:
    if not API_KEY or not TOKEN:
        raise RuntimeError("API_KEY ou TOKEN nao foram carregados. Confira o arquivo .env.")


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
        fields="id,name,shortLink,url,dateLastActivity",
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Erro ao acessar a lista no Trello. "
            f"Lista: {id_lista}. Status: {response.status_code}. Resposta: {response.text}"
        )

    return response.json()


def normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().lower().split())


def encontrar_duplicados(cartoes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    cartoes_por_nome: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for cartao in cartoes:
        nome_normalizado = normalizar_nome(cartao.get("name", ""))
        if nome_normalizado:
            cartoes_por_nome[nome_normalizado].append(cartao)

    return {
        nome: grupo
        for nome, grupo in cartoes_por_nome.items()
        if len(grupo) > 1
    }


def montar_relatorio(
    cartoes: list[dict[str, Any]],
    duplicados: dict[str, list[dict[str, Any]]],
) -> str:
    data_relatorio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total_cartoes_duplicados = sum(len(grupo) for grupo in duplicados.values())

    linhas = [
        "RELATORIO DE CARTOES COM NOMES REPETIDOS",
        "=" * 60,
        f"Gerado em: {data_relatorio}",
        f"Lista analisada: Projetos/Solicitacoes ({LISTA_PROJETO_SOLICITACOES})",
        f"Total de cartoes analisados: {len(cartoes)}",
        f"Total de nomes repetidos: {len(duplicados)}",
        f"Total de cartoes envolvidos em repeticao: {total_cartoes_duplicados}",
        "=" * 60,
        "",
    ]

    if not duplicados:
        linhas.append("Nenhum cartao com nome repetido foi encontrado.")
        return "\n".join(linhas)

    for indice, grupo in enumerate(
        sorted(duplicados.values(), key=lambda item: item[0].get("name", "").lower()),
        start=1,
    ):
        nome_exibicao = grupo[0].get("name", "Sem nome")
        linhas.append(f"{indice}. {nome_exibicao}")
        linhas.append(f"   Quantidade: {len(grupo)}")

        for cartao in sorted(grupo, key=lambda item: item.get("dateLastActivity", "")):
            linhas.append(f"   - URL: {cartao.get('url', 'Sem URL')}")
            linhas.append(f"     ID: {cartao.get('id', 'Sem ID')}")
            linhas.append(
                "     Ultima atividade: "
                f"{cartao.get('dateLastActivity', 'Sem data informada')}"
            )

        linhas.append("")

    return "\n".join(linhas)


def salvar_relatorio(conteudo: str) -> str:
    pasta_relatorios = os.path.join(os.path.dirname(__file__), "relatorios_gerados")
    os.makedirs(pasta_relatorios, exist_ok=True)

    data_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_duplicados_projetos_{data_arquivo}.txt"
    caminho_arquivo = os.path.join(pasta_relatorios, nome_arquivo)

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
        arquivo.write("\n")

    return caminho_arquivo


def gerar_relatorio_duplicados() -> None:
    validar_configuracao()

    print("Gerando relatorio de duplicados na lista de Projetos/Solicitacoes...")
    cartoes = buscar_cartoes_lista(LISTA_PROJETO_SOLICITACOES)
    duplicados = encontrar_duplicados(cartoes)
    relatorio = montar_relatorio(cartoes, duplicados)
    caminho_relatorio = salvar_relatorio(relatorio)
    total_cartoes_duplicados = sum(len(grupo) for grupo in duplicados.values())

    print(f"Relatorio salvo em: {caminho_relatorio}")
    print(
        "Resumo: "
        f"{len(cartoes)} cartoes analisados, "
        f"{len(duplicados)} nomes repetidos, "
        f"{total_cartoes_duplicados} cartoes envolvidos."
    )
    print("Observacao: nenhum cartao foi alterado.")


if __name__ == "__main__":
    gerar_relatorio_duplicados()
