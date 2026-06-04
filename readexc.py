import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv


caminho_env = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(caminho_env)

API_KEY = os.getenv("API_KEY")
TOKEN = os.getenv("TOKEN")

# --- CONFIGURACAO DE LISTAS ---
LISTA_EXECUCAO = "6669a6666762039572b85c2d"  # Lista "Execucao" no quadro Solicitacoes 3.0
LISTA_OBRA_PROJETOS = "66a3cd53fa0cf67309404be0"  # Lista "Obra" no quadro Projetos
LISTA_FINALIZADOS_PROJETOS = "66a3cd4cf460377406141493"  # Lista "Finalizados" no quadro Projetos

TRELLO_API = "https://api.trello.com/1"
TIMEOUT = 20
MAX_TENTATIVAS = 3
INTERVALO_ENTRE_REQUISICOES = 0.2


@dataclass
class ResultadoSolicitacao:
    nome: str
    status: str
    motivo: str
    projeto: str | None = None
    implantacao: str | None = None
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


def buscar_cartao(
    shortlink_ou_id: str,
    incluir_anexos: bool = False,
) -> tuple[dict[str, Any] | None, requests.Response]:
    response = requisicao_trello(
        "GET",
        f"/cards/{shortlink_ou_id}",
        attachments=str(incluir_anexos).lower(),
        fields="id,name,idList,idBoard,closed,dueComplete,labels,shortLink,url",
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


def tem_etiqueta_vistoriado(cartao: dict[str, Any]) -> bool:
    for etiqueta in cartao.get("labels", []):
        nome = etiqueta.get("name", "").strip().lower()
        if nome == "vistoriado":
            return True

    return False


def implantacao_concluida(cartao_implantacao: dict[str, Any]) -> tuple[bool, str]:
    if cartao_implantacao.get("dueComplete") is True:
        return True, "data marcada como concluida"

    if tem_etiqueta_vistoriado(cartao_implantacao):
        return True, "etiqueta Vistoriado"

    return False, "sem data concluida e sem etiqueta Vistoriado"


def analisar_solicitacao(cartao_pai: dict[str, Any]) -> ResultadoSolicitacao:
    nome_pai = cartao_pai.get("name", "Sem nome")
    shortlinks_projetos = shortlinks_dos_anexos(cartao_pai)

    if not shortlinks_projetos:
        return ResultadoSolicitacao(
            nome=nome_pai,
            status="SEM_PROJETO",
            motivo="cartao da Execucao sem anexo Trello de projeto",
        )

    erros: list[str] = []
    pendencias: list[ResultadoSolicitacao] = []
    aguardando_obra: ResultadoSolicitacao | None = None
    projetos_fora_do_fluxo: list[str] = []

    for shortlink_projeto in shortlinks_projetos:
        projeto, response_projeto = buscar_cartao(shortlink_projeto, incluir_anexos=True)

        if projeto is None:
            erros.append(
                f"erro {response_projeto.status_code} ao ler projeto {shortlink_projeto}: "
                f"{response_projeto.text}"
            )
            continue

        nome_projeto = projeto.get("name", "Projeto sem nome")

        if projeto.get("idList") == LISTA_OBRA_PROJETOS:
            aguardando_obra = ResultadoSolicitacao(
                nome=nome_pai,
                status="AGUARDANDO_OBRA",
                motivo="projeto esta na lista Obra",
                projeto=nome_projeto,
            )
            continue

        if projeto.get("idList") != LISTA_FINALIZADOS_PROJETOS:
            projetos_fora_do_fluxo.append(
                f"{nome_projeto} esta na lista {projeto.get('idList')}"
            )

        shortlinks_implantacoes = shortlinks_dos_anexos(projeto)

        if not shortlinks_implantacoes:
            pendencias.append(
                ResultadoSolicitacao(
                    nome=nome_pai,
                    status="SEM_IMPLANTACAO",
                    motivo="projeto sem anexo Trello de implantacao",
                    projeto=nome_projeto,
                )
            )
            continue

        for shortlink_implantacao in shortlinks_implantacoes:
            implantacao, response_implantacao = buscar_cartao(shortlink_implantacao)

            if implantacao is None:
                erros.append(
                    f"erro {response_implantacao.status_code} ao ler implantacao "
                    f"{shortlink_implantacao}: {response_implantacao.text}"
                )
                continue

            concluida, motivo = implantacao_concluida(implantacao)
            nome_implantacao = implantacao.get("name", "Implantacao sem nome")

            if concluida:
                return ResultadoSolicitacao(
                    nome=nome_pai,
                    status="CONCLUIDO",
                    motivo=motivo,
                    projeto=nome_projeto,
                    implantacao=nome_implantacao,
                    detalhes=list(projetos_fora_do_fluxo),
                )

            pendencias.append(
                ResultadoSolicitacao(
                    nome=nome_pai,
                    status="PENDENTE",
                    motivo=motivo,
                    projeto=nome_projeto,
                    implantacao=nome_implantacao,
                    detalhes=list(projetos_fora_do_fluxo),
                )
            )

    if aguardando_obra:
        aguardando_obra.detalhes = list(projetos_fora_do_fluxo)
        return aguardando_obra

    if pendencias:
        pendente = pendencias[0]
        pendente.detalhes = list(dict.fromkeys([*pendente.detalhes, *projetos_fora_do_fluxo]))
        return pendente

    if erros:
        return ResultadoSolicitacao(
            nome=nome_pai,
            status="ERRO",
            motivo="; ".join(erros),
            detalhes=projetos_fora_do_fluxo,
        )

    return ResultadoSolicitacao(
        nome=nome_pai,
        status="SEM_PROJETO_VALIDO",
        motivo="anexos Trello encontrados, mas nenhum projeto pode ser analisado",
        detalhes=projetos_fora_do_fluxo,
    )


def formatar_resultado(resultado: ResultadoSolicitacao) -> str:
    rotulos = {
        "CONCLUIDO": "[CONCLUIDO]",
        "AGUARDANDO_OBRA": "[AGUARDANDO OBRA]",
        "PENDENTE": "[PENDENTE]",
        "SEM_PROJETO": "[SEM PROJETO ANEXADO]",
        "SEM_IMPLANTACAO": "[SEM IMPLANTACAO]",
        "SEM_PROJETO_VALIDO": "[SEM PROJETO VALIDO]",
        "ERRO": "[ERRO DE LEITURA]",
    }

    partes = [f"{rotulos.get(resultado.status, '[STATUS DESCONHECIDO]'):24} {resultado.nome}"]

    if resultado.projeto:
        partes.append(f"Projeto: {resultado.projeto}")
    if resultado.implantacao:
        partes.append(f"Implantacao: {resultado.implantacao}")

    partes.append(f"Motivo: {resultado.motivo}")

    if resultado.detalhes:
        partes.append("Detalhes: " + " | ".join(resultado.detalhes))

    return " - ".join(partes)


def salvar_relatorio(conteudo: str) -> str:
    pasta_relatorios = os.path.join(os.path.dirname(__file__), "relatorios_gerados")
    os.makedirs(pasta_relatorios, exist_ok=True)

    data_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = os.path.join(
        pasta_relatorios,
        f"relatorio_execucao_{data_arquivo}.txt",
    )

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
        arquivo.write("\n")

    return caminho_arquivo


def gerar_relatorio_inteligente() -> None:
    validar_configuracao()

    print("Gerando relatorio da lista de Execucao...")
    solicitacoes_pai = buscar_cartoes_lista(LISTA_EXECUCAO)

    totais = {
        "CONCLUIDO": 0,
        "AGUARDANDO_OBRA": 0,
        "PENDENTE": 0,
        "SEM_PROJETO": 0,
        "SEM_IMPLANTACAO": 0,
        "SEM_PROJETO_VALIDO": 0,
        "ERRO": 0,
    }

    linhas_detalhamento = [
        "DETALHAMENTO DOS CARTOES",
        "-" * 100,
    ]

    for cartao_pai in solicitacoes_pai:
        resultado = analisar_solicitacao(cartao_pai)
        totais[resultado.status] = totais.get(resultado.status, 0) + 1
        linhas_detalhamento.append(formatar_resultado(resultado))

    total_analisados = len(solicitacoes_pai)
    total_sem_vinculo = (
        totais["SEM_PROJETO"] + totais["SEM_IMPLANTACAO"] + totais["SEM_PROJETO_VALIDO"]
    )
    total_somado = sum(totais.values())
    data_relatorio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    linhas_resumo = [
        "=" * 60,
        "RELATORIO DE STATUS DA EXECUCAO",
        "=" * 60,
        f"Gerado em: {data_relatorio}",
        f"Total de solicitacoes na lista:  {total_analisados}",
        "-" * 60,
        f"Implantacoes concluidas:         {totais['CONCLUIDO']}",
        f"Aguardando obra:                 {totais['AGUARDANDO_OBRA']}",
        f"Implantacoes pendentes:          {totais['PENDENTE']}",
        f"Cartoes sem vinculo completo:    {total_sem_vinculo}",
        f"Erros de leitura da API:         {totais['ERRO']}",
        "-" * 60,
        f"Validacao matematica: Soma = {total_somado} (deve ser igual a {total_analisados})",
        "=" * 60,
    ]

    relatorio = "\n".join([*linhas_resumo, "", *linhas_detalhamento])
    caminho_relatorio = salvar_relatorio(relatorio)

    print(f"Relatorio salvo em: {caminho_relatorio}")
    print(
        "Resumo: "
        f"{total_analisados} solicitacoes analisadas, "
        f"{totais['CONCLUIDO']} concluidas, "
        f"{totais['PENDENTE']} pendentes."
    )


if __name__ == "__main__":
    gerar_relatorio_inteligente()
