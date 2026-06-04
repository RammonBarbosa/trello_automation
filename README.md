# Automacao de Fluxo Kanban no Trello

Projeto em Python criado para automatizar e auditar um fluxo operacional no Trello, reduzindo verificacoes manuais entre listas de solicitacoes, projetos, execucao e implantacao.

A automacao monitora cartoes de solicitacoes, identifica cartoes vinculados por anexos e move automaticamente a solicitacao principal para a lista de execucao quando pelo menos um projeto relacionado e concluido. O projeto tambem possui relatorios auxiliares para acompanhar pendencias, implantacoes e duplicidades.

## Problema Resolvido

Em fluxos com multiplos quadros, setores e etapas, acompanhar manualmente o status de cartoes relacionados pode gerar atrasos, retrabalho e falhas de comunicacao.

Este projeto resolve esse gargalo ao integrar listas do Trello via API, criando regras automatizadas e relatorios de apoio para tomada de decisao.

## Principais Funcionalidades

- Movimentacao automatica de solicitacoes para a lista de execucao.
- Verificacao de cartoes anexados como projetos relacionados.
- Relatorio de solicitacoes prontas para execucao.
- Relatorio de status dos cartoes na lista de execucao.
- Relatorio de possiveis cartoes duplicados na lista de projetos.
- Extracao de shortlinks de URLs do Trello com expressao regular.
- Tratamento de falhas de conexao e novas tentativas em requisicoes HTTP.
- Controle de cadencia entre chamadas para reduzir risco de rate limiting.
- Geracao de relatorios em arquivos `.txt`.
- Saida enxuta no terminal, mostrando apenas resumo e caminho do relatorio.

## Tecnologias Utilizadas

- Python 3
- Requests
- Python-dotenv
- Trello REST API

## Estrutura do Projeto

```text
.
|-- main.py
|-- moveproj.py
|-- readproj.py
|-- readexc.py
|-- duplicates.py
|-- requirements.txt
`-- README.md
```

## Scripts

| Arquivo | Finalidade |
| --- | --- |
| `main.py` | Menu principal para executar relatorios e automacao em um unico ponto de entrada. |
| `moveproj.py` | Automacao principal. Move solicitacoes para execucao quando algum projeto anexado esta finalizado. |
| `readproj.py` | Gera relatorio de solicitacoes/projetos prontos para execucao. |
| `readexc.py` | Gera relatorio de status dos cartoes que ja estao na lista de execucao. |
| `duplicates.py` | Gera relatorio de possiveis cartoes duplicados na lista de projetos/solicitacoes. |

## Como Funciona

1. O script consulta cartoes em listas especificas do Trello.
2. Para cada cartao, busca anexos que sejam links de outros cartoes Trello.
3. O shortlink do cartao anexado e extraido da URL.
4. A API do Trello e consultada para verificar status, lista, etiquetas e conclusoes.
5. A automacao move cartoes quando a regra de negocio e atendida.
6. Os relatorios sao salvos em arquivos `.txt` dentro de `relatorios_gerados`.

## Configuracao

Crie um arquivo `.env` na raiz do projeto com suas credenciais da API do Trello:

```env
API_KEY=sua_api_key_aqui
TOKEN=seu_token_aqui
```

As credenciais podem ser geradas na area de desenvolvedor do Trello.

## Instalacao

Clone o repositorio:

```bash
git clone https://github.com/SeuUsuario/trello_automation.git
cd trello_automation
```

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Execucao

Para abrir o menu principal:

```bash
python main.py
```

Tambem e possivel executar cada rotina individualmente:

```bash
python readproj.py
python readexc.py
python duplicates.py
python moveproj.py
```

## Relatorios Gerados

Os relatorios sao salvos automaticamente na pasta:

```text
relatorios_gerados/
```

Exemplos de arquivos:

```text
relatorio_projetos_prontos_20260604_133000.txt
relatorio_execucao_20260604_133000.txt
relatorio_duplicados_projetos_20260604_133000.txt
relatorio_automacao_movimentacao_20260604_133000.txt
```

No terminal, a execucao mostra apenas um resumo curto e o caminho do arquivo gerado.

## Decisoes Tecnicas

- Uso de variaveis de ambiente para evitar exposicao de credenciais.
- Separacao entre automacao de movimentacao e relatorios operacionais.
- Requisicoes com timeout para evitar travamentos indefinidos.
- Mecanismo de retry para lidar com falhas temporarias de conexao.
- Respeito ao rate limit da API por meio de pausas entre requisicoes.
- Relatorios persistidos em `.txt` para auditoria e consulta posterior.
- Menu central em `main.py` para facilitar o uso do projeto.

## Competencias Demonstradas

Este projeto demonstra habilidades relevantes para automacao de processos e integracao de sistemas:

- Consumo de APIs REST.
- Automacao de fluxos operacionais.
- Tratamento de erros em integracoes externas.
- Manipulacao de dados retornados por APIs.
- Uso seguro de variaveis de ambiente.
- Organizacao de scripts Python para rotinas internas.
- Criacao de relatorios para apoio a tomada de decisao.

## Possiveis Melhorias Futuras

- Modularizar o codigo em pacotes como `config`, `trello_client`, `automacoes` e `relatorios`.
- Parametrizar os IDs das listas do Trello via `.env`.
- Adicionar logs estruturados.
- Criar testes automatizados para funcoes de extracao e validacao.
- Agendar a execucao recorrente com Task Scheduler, cron ou servico em nuvem.
- Criar um dashboard para visualizar os relatorios gerados.

## Observacao de Seguranca

Nao publique o arquivo `.env` no repositorio. Ele contem credenciais sensiveis de acesso a API do Trello.

## Autor

Projeto em desenvolvimento como solucao pratica de automacao para otimizar um fluxo real de solicitacoes, projetos e execucao dentro do Trello.
