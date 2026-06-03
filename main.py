import os
import re
import time

import requests
from dotenv import load_dotenv


load_dotenv()

# --- CONFIGURACOES ---
API_KEY = os.getenv("API_KEY")
TOKEN = os.getenv("TOKEN")

LISTA_PROJETO_SOLICITACOES = "6669a662923d4751850ae26a"
LISTA_FINALIZADO_PROJETOS = "66a3cd4cf460377406141493"
LISTA_EXECUCAO = "6669a6666762039572b85c2d"

TRELLO_API = "https://api.trello.com/1"
TIMEOUT = 20
MAX_TENTATIVAS = 3


def validar_configuracao():
    if not API_KEY or not TOKEN:
        raise RuntimeError(
            "API_KEY ou TOKEN nao foram carregados. Confira o arquivo .env."
        )


def extrair_shortlink_trello(url):
    if not url:
        return None

    match = re.search(r"trello\.com/c/([^/?#]+)", url, flags=re.IGNORECASE)
    if not match:
        return None

    return match.group(1)


def requisicao_trello(metodo, caminho, **params):
    url = f"{TRELLO_API}{caminho}"
    params = {"key": API_KEY, "token": TOKEN, **params}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            response = requests.request(
                metodo,
                url,
                params=params,
                timeout=TIMEOUT,
            )
        except requests.RequestException as erro:
            if tentativa == MAX_TENTATIVAS:
                raise RuntimeError(f"Falha de conexao com o Trello: {erro}") from erro

            print(f"Falha de conexao. Tentando novamente ({tentativa}/{MAX_TENTATIVAS})...")
            time.sleep(2 * tentativa)
            continue

        if response.status_code != 429:
            return response

        espera = int(response.headers.get("Retry-After", "10"))
        print(f"Rate limit do Trello. Aguardando {espera}s antes de tentar novamente...")
        time.sleep(espera)

    return response


def buscar_cartoes_solicitacoes():
    response = requisicao_trello(
        "GET",
        f"/lists/{LISTA_PROJETO_SOLICITACOES}/cards",
        attachments="true",
        fields="id,name,idList",
    )

    if response.status_code != 200:
        raise RuntimeError(
            "O Trello barrou o acesso aos cartoes da lista de solicitacoes. "
            f"Status: {response.status_code}. Resposta: {response.text}"
        )

    return response.json()


def buscar_cartao_vinculado(shortlink):
    response = requisicao_trello(
        "GET",
        f"/cards/{shortlink}",
        fields="id,name,idList,idBoard,closed,shortLink,url",
    )

    if response.status_code != 200:
        return None, response

    return response.json(), response


def mover_cartao_para_execucao(cartao):
    return requisicao_trello(
        "PUT",
        f"/cards/{cartao['id']}",
        idList=LISTA_EXECUCAO,
    )


def rodar_automacao_flexivel():
    validar_configuracao()

    print("Iniciando verificacao: basta um anexo Trello estar finalizado.")

    solicitacoes = buscar_cartoes_solicitacoes()

    cartoes_movidos = 0
    cartoes_sem_anexo_trello = 0
    cartoes_sem_anexo_finalizado = 0
    falhas_consulta_anexo = 0
    falhas_movimento = 0

    for cartao in solicitacoes:
        anexos_trello = []

        for anexo in cartao.get("attachments", []):
            url = anexo.get("url", "")
            shortlink = extrair_shortlink_trello(url)

            if shortlink:
                anexos_trello.append({"shortlink": shortlink, "url": url})

        if not anexos_trello:
            cartoes_sem_anexo_trello += 1
            print(f"Sem anexo Trello: '{cartao['name']}'")
            continue

        anexo_finalizado = None

        for anexo in anexos_trello:
            dados_vinculado, response = buscar_cartao_vinculado(anexo["shortlink"])

            if dados_vinculado is None:
                falhas_consulta_anexo += 1
                print(
                    "Falha ao consultar anexo "
                    f"{anexo['shortlink']} do cartao '{cartao['name']}'. "
                    f"Status: {response.status_code}. Resposta: {response.text}"
                )
                continue

            if dados_vinculado.get("idList") == LISTA_FINALIZADO_PROJETOS:
                anexo_finalizado = dados_vinculado
                break

            print(
                f"Anexo ainda nao finalizado: '{dados_vinculado.get('name')}' "
                f"esta na lista {dados_vinculado.get('idList')}."
            )

        if not anexo_finalizado:
            cartoes_sem_anexo_finalizado += 1
            print(
                f"'{cartao['name']}': nenhum dos {len(anexos_trello)} "
                "anexos Trello esta na lista de finalizados."
            )
            continue

        print(
            f"Anexo finalizado encontrado: '{anexo_finalizado['name']}'. "
            f"Movendo '{cartao['name']}' para Execucao..."
        )

        response_move = mover_cartao_para_execucao(cartao)

        if response_move.status_code == 200:
            cartoes_movidos += 1
            print(f"Movido com sucesso: '{cartao['name']}'")
        else:
            falhas_movimento += 1
            print(
                f"Falha ao mover '{cartao['name']}'. "
                f"Status: {response_move.status_code}. Resposta: {response_move.text}"
            )

    print("\n" + "=" * 50)
    print("RELATORIO FINAL DA AUTOMACAO")
    print(f"Total de cartoes lidos: {len(solicitacoes)}")
    print(f"Movidos para Execucao: {cartoes_movidos}")
    print(f"Sem anexo Trello: {cartoes_sem_anexo_trello}")
    print(f"Sem anexo finalizado: {cartoes_sem_anexo_finalizado}")
    print(f"Falhas ao consultar anexos: {falhas_consulta_anexo}")
    print(f"Falhas ao mover cartoes: {falhas_movimento}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    rodar_automacao_flexivel()
