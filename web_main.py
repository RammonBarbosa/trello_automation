import contextlib
import html
import io
import os
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from duplicates import gerar_relatorio_duplicados
from moveproj import rodar_automacao_flexivel
from readexc import gerar_relatorio_inteligente
from readproj import gerar_relatorio_projetos


PORTA_PADRAO = 8000
PASTA_BASE = os.path.dirname(__file__)
PASTA_RELATORIOS = os.path.join(PASTA_BASE, "relatorios_gerados")

ROTINAS = {
    "projetos": {
        "titulo": "Projetos prontos",
        "subtitulo": "Solicitacoes com projeto finalizado para execucao.",
        "acao": gerar_relatorio_projetos,
        "classe": "success",
    },
    "execucao": {
        "titulo": "Lista de execucao",
        "subtitulo": "Status de implantacao, obra e pendencias.",
        "acao": gerar_relatorio_inteligente,
        "classe": "info",
    },
    "duplicados": {
        "titulo": "Duplicados",
        "subtitulo": "Cartoes com nomes repetidos em projetos/solicitacoes.",
        "acao": gerar_relatorio_duplicados,
        "classe": "warning",
    },
    "mover": {
        "titulo": "Mover para execucao",
        "subtitulo": "Executa a automacao que altera cartoes no Trello.",
        "acao": rodar_automacao_flexivel,
        "classe": "danger",
    },
}


ULTIMA_EXECUCAO = {
    "rotina": None,
    "quando": None,
    "status": None,
    "saida": "Nenhuma rotina executada nesta sessao.",
}


def listar_relatorios() -> list[dict[str, str]]:
    if not os.path.isdir(PASTA_RELATORIOS):
        return []

    relatorios = []
    for nome in os.listdir(PASTA_RELATORIOS):
        caminho = os.path.join(PASTA_RELATORIOS, nome)
        if not os.path.isfile(caminho):
            continue

        relatorios.append(
            {
                "nome": nome,
                "modificado": datetime.fromtimestamp(os.path.getmtime(caminho)).strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
                "tamanho": f"{os.path.getsize(caminho) / 1024:.1f} KB",
            }
        )

    return sorted(relatorios, key=lambda item: item["modificado"], reverse=True)


def executar_rotina(codigo: str) -> None:
    rotina = ROTINAS.get(codigo)
    if not rotina:
        ULTIMA_EXECUCAO.update(
            {
                "rotina": "Opcao invalida",
                "quando": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "status": "erro",
                "saida": "A rotina solicitada nao existe.",
            }
        )
        return

    buffer = io.StringIO()
    status = "sucesso"

    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            rotina["acao"]()
        except Exception as erro:  # noqa: BLE001 - exibido ao operador no dashboard.
            status = "erro"
            print(f"Erro ao executar rotina: {erro}")

    ULTIMA_EXECUCAO.update(
        {
            "rotina": rotina["titulo"],
            "quando": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "status": status,
            "saida": buffer.getvalue().strip() or "Rotina finalizada sem mensagens.",
        }
    )


def tag_status(status: str | None) -> str:
    if status == "sucesso":
        return '<span class="status ok">Sucesso</span>'
    if status == "erro":
        return '<span class="status error">Erro</span>'
    return '<span class="status neutral">Aguardando</span>'


def montar_html() -> bytes:
    relatorios = listar_relatorios()
    cards_rotinas = []

    for codigo, rotina in ROTINAS.items():
        confirmacao = ""
        if codigo == "mover":
            confirmacao = (
                'data-confirm="Esta rotina pode mover cartoes no Trello. Continuar?"'
            )

        cards_rotinas.append(
            f"""
            <article class="routine {rotina['classe']}">
                <div>
                    <p class="eyebrow">{html.escape(codigo)}</p>
                    <h2>{html.escape(rotina['titulo'])}</h2>
                    <p>{html.escape(rotina['subtitulo'])}</p>
                </div>
                <form method="post" action="/executar">
                    <input type="hidden" name="rotina" value="{html.escape(codigo)}">
                    <button type="submit" {confirmacao}>Executar</button>
                </form>
            </article>
            """
        )

    linhas_relatorios = []
    for relatorio in relatorios[:12]:
        nome = html.escape(relatorio["nome"])
        linhas_relatorios.append(
            f"""
            <tr>
                <td><a href="/relatorio/{nome}" target="_blank">{nome}</a></td>
                <td>{html.escape(relatorio['modificado'])}</td>
                <td>{html.escape(relatorio['tamanho'])}</td>
            </tr>
            """
        )

    if not linhas_relatorios:
        linhas_relatorios.append(
            """
            <tr>
                <td colspan="3" class="empty">Nenhum relatorio encontrado.</td>
            </tr>
            """
        )

    ultima_saida = html.escape(ULTIMA_EXECUCAO["saida"])
    ultima_rotina = html.escape(ULTIMA_EXECUCAO["rotina"] or "Sem execucao")
    ultima_quando = html.escape(ULTIMA_EXECUCAO["quando"] or "-")

    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Automacao Trello</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f4f7fb;
            --panel: #ffffff;
            --line: #d9e1ec;
            --text: #172033;
            --muted: #667085;
            --blue: #1f6feb;
            --green: #16845b;
            --yellow: #9a6700;
            --red: #c93c37;
            --shadow: 0 14px 38px rgba(22, 32, 51, 0.08);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background: var(--bg);
            color: var(--text);
            font-family: Arial, Helvetica, sans-serif;
        }}

        header {{
            border-bottom: 1px solid var(--line);
            background: #0f172a;
            color: #ffffff;
        }}

        .header-inner,
        main {{
            width: min(1180px, calc(100% - 32px));
            margin: 0 auto;
        }}

        .header-inner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            padding: 28px 0;
        }}

        h1 {{
            margin: 0;
            font-size: clamp(28px, 4vw, 44px);
            line-height: 1;
            letter-spacing: 0;
        }}

        .subtitle {{
            margin: 8px 0 0;
            color: #cbd5e1;
            font-size: 15px;
        }}

        .header-metric {{
            min-width: 180px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 8px;
            padding: 14px 16px;
            text-align: right;
        }}

        .header-metric strong {{
            display: block;
            font-size: 28px;
        }}

        .header-metric span {{
            color: #cbd5e1;
            font-size: 13px;
        }}

        main {{
            padding: 28px 0 42px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
        }}

        .routine,
        .panel {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: var(--shadow);
        }}

        .routine {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 230px;
            padding: 18px;
            border-top: 5px solid var(--blue);
        }}

        .routine.success {{ border-top-color: var(--green); }}
        .routine.info {{ border-top-color: var(--blue); }}
        .routine.warning {{ border-top-color: var(--yellow); }}
        .routine.danger {{ border-top-color: var(--red); }}

        .eyebrow {{
            margin: 0 0 12px;
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        h2 {{
            margin: 0 0 10px;
            font-size: 21px;
            letter-spacing: 0;
        }}

        .routine p:not(.eyebrow) {{
            margin: 0;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.5;
        }}

        button {{
            width: 100%;
            min-height: 42px;
            border: 0;
            border-radius: 6px;
            background: #172033;
            color: #ffffff;
            cursor: pointer;
            font-weight: 700;
            font-size: 14px;
        }}

        button:hover {{
            background: #25324a;
        }}

        .content {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 16px;
            margin-top: 16px;
        }}

        .panel {{
            min-width: 0;
            padding: 18px;
        }}

        .panel-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }}

        .panel-head h2 {{
            margin: 0;
        }}

        .status {{
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 700;
        }}

        .status.ok {{
            background: #dff7ed;
            color: #116149;
        }}

        .status.error {{
            background: #ffe5e3;
            color: #9f2c28;
        }}

        .status.neutral {{
            background: #eef2f7;
            color: #475467;
        }}

        .meta {{
            display: flex;
            gap: 12px;
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 12px;
        }}

        pre {{
            width: 100%;
            min-height: 240px;
            max-height: 420px;
            overflow: auto;
            margin: 0;
            border-radius: 8px;
            background: #0b1220;
            color: #dbeafe;
            padding: 16px;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.5;
            font-size: 13px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th,
        td {{
            border-bottom: 1px solid var(--line);
            padding: 11px 8px;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
        }}

        a {{
            color: var(--blue);
            font-weight: 700;
            text-decoration: none;
            word-break: break-word;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .empty {{
            color: var(--muted);
            text-align: center;
        }}

        @media (max-width: 980px) {{
            .grid,
            .content {{
                grid-template-columns: 1fr 1fr;
            }}

            .content {{
                display: block;
            }}

            .content .panel + .panel {{
                margin-top: 16px;
            }}
        }}

        @media (max-width: 640px) {{
            .header-inner {{
                display: block;
            }}

            .header-metric {{
                margin-top: 18px;
                text-align: left;
            }}

            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div>
                <h1>Automacao Trello</h1>
                <p class="subtitle">Painel local para executar rotinas e consultar relatorios.</p>
            </div>
            <div class="header-metric">
                <strong>{len(relatorios)}</strong>
                <span>relatorios gerados</span>
            </div>
        </div>
    </header>

    <main>
        <section class="grid">
            {''.join(cards_rotinas)}
        </section>

        <section class="content">
            <article class="panel">
                <div class="panel-head">
                    <h2>Ultima execucao</h2>
                    {tag_status(ULTIMA_EXECUCAO["status"])}
                </div>
                <div class="meta">
                    <span>{ultima_rotina}</span>
                    <span>{ultima_quando}</span>
                </div>
                <pre>{ultima_saida}</pre>
            </article>

            <article class="panel">
                <div class="panel-head">
                    <h2>Relatorios</h2>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Arquivo</th>
                            <th>Gerado em</th>
                            <th>Tamanho</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(linhas_relatorios)}
                    </tbody>
                </table>
            </article>
        </section>
    </main>

    <script>
        document.querySelectorAll("button[data-confirm]").forEach((button) => {{
            button.addEventListener("click", (event) => {{
                if (!confirm(button.dataset.confirm)) {{
                    event.preventDefault();
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    return pagina.encode("utf-8")


class TrelloDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            self.responder(200, montar_html(), "text/html; charset=utf-8")
            return

        if self.path.startswith("/relatorio/"):
            nome = self.path.removeprefix("/relatorio/")
            caminho = os.path.abspath(os.path.join(PASTA_RELATORIOS, nome))
            pasta_segura = os.path.abspath(PASTA_RELATORIOS)

            if not caminho.startswith(pasta_segura) or not os.path.isfile(caminho):
                self.responder(404, b"Relatorio nao encontrado.", "text/plain; charset=utf-8")
                return

            with open(caminho, "rb") as arquivo:
                self.responder(200, arquivo.read(), "text/plain; charset=utf-8")
            return

        self.responder(404, b"Pagina nao encontrada.", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/executar":
            self.responder(404, b"Pagina nao encontrada.", "text/plain; charset=utf-8")
            return

        tamanho = int(self.headers.get("Content-Length", "0"))
        dados = parse_qs(self.rfile.read(tamanho).decode("utf-8"))
        executar_rotina(dados.get("rotina", [""])[0])
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def responder(self, status: int, conteudo: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def log_message(self, format: str, *args: object) -> None:
        return


def iniciar_dashboard(porta: int = PORTA_PADRAO, abrir_navegador: bool = True) -> None:
    endereco = ("127.0.0.1", porta)
    servidor = ThreadingHTTPServer(endereco, TrelloDashboardHandler)
    url = f"http://{endereco[0]}:{endereco[1]}"

    print(f"Dashboard disponivel em: {url}")
    print("Pressione Ctrl+C para encerrar.")

    if abrir_navegador:
        webbrowser.open(url)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar_dashboard()
