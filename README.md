# Automacao de Fluxo Kanban no Trello

Projeto em Python criado para automatizar a movimentacao de cartoes entre listas do Trello, reduzindo verificacoes manuais em um fluxo operacional baseado em Kanban.

A automacao monitora cartoes de solicitacoes, identifica cartoes de projetos anexados e move automaticamente a solicitacao principal para a etapa de execucao quando pelo menos um projeto relacionado e concluido.

## Problema Resolvido

Em fluxos com multiplos quadros, setores e etapas, acompanhar manualmente o status de cartoes relacionados pode gerar atrasos, retrabalho e falhas de comunicacao.

Este projeto resolve esse gargalo ao integrar listas do Trello via API, criando uma regra automatizada para avancar solicitacoes assim que uma condicao de negocio e atendida.

## Principais Funcionalidades

- Consulta automatica de cartoes em listas especificas do Trello.
- Leitura de anexos para identificar cartoes vinculados.
- Extracao de shortlinks de URLs do Trello com expressao regular.
- Verificacao do status de cartoes relacionados em outro quadro/lista.
- Movimentacao automatica do cartao principal para a lista de execucao.
- Tratamento de falhas de conexao e novas tentativas em requisicoes HTTP.
- Controle de cadencia entre chamadas para reduzir risco de rate limiting.
- Relatorios no terminal com totais de cartoes lidos, movidos e pendencias encontradas.
- Scripts auxiliares para analise de solicitacoes, projetos e duplicidades.

## Tecnologias Utilizadas

- Python 3
- Requests
- Python-dotenv
- Trello REST API

## Estrutura do Projeto

```text
.
|-- automacao_trello.py
|-- readexc.py
|-- readproj.py
|-- relatorio_duplicados_projetos.py
`-- README.md
```

## Scripts

| Arquivo | Finalidade |
| --- | --- |
| `automacao_trello.py` | Script principal da automacao. Verifica cartoes anexados e move solicitacoes para execucao quando a regra e atendida. |
| `readproj.py` | Analisa solicitacoes e seus projetos anexados, gerando uma visao de status para acompanhamento. |
| `readexc.py` | Analisa cartoes em execucao e valida vinculos com projetos/implantacao. |
| `duplicates.py` | Identifica possiveis cartoes duplicados na lista de projetos/solicitacoes. |

## Como Funciona

1. O script consulta os cartoes de uma lista de solicitacoes no Trello.
2. Para cada cartao, busca anexos que sejam links de cartoes Trello.
3. O shortlink do cartao anexado e extraido da URL.
4. A API do Trello e consultada para verificar em qual lista o cartao anexado esta.
5. Se algum cartao anexado estiver na lista de projetos finalizados, a solicitacao principal e movida para a lista de execucao.
6. Ao final, o terminal exibe um relatorio com os resultados da execucao.

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
pip install requests python-dotenv
```

## Execucao

Para executar a automacao principal:

```bash
python automacao_trello.py
```

Para executar os scripts auxiliares:

```bash
python readproj.py
python readexc.py
python duplicates.py
```

## Exemplo de Saida

```text
RELATORIO FINAL DA AUTOMACAO
Total de cartoes lidos: 42
Movidos para Execucao: 7
Sem anexo Trello: 3
Sem anexo finalizado: 32
Falhas ao consultar anexos: 0
Falhas ao mover cartoes: 0
```

## Decisoes Tecnicas

- Uso de variaveis de ambiente para evitar exposicao de credenciais.
- Separacao entre automacao principal e scripts de apoio para analise operacional.
- Requisicoes com timeout para evitar travamentos indefinidos.
- Mecanismo de retry para lidar com falhas temporarias de conexao.
- Respeito ao rate limit da API por meio de pausas entre requisicoes.
- Validacao previa das credenciais antes de iniciar o processo.
- Relatorios simples no terminal para facilitar auditoria e acompanhamento.

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

- Criar um arquivo `requirements.txt` para padronizar a instalacao.
- Parametrizar os IDs das listas do Trello via `.env`.
- Adicionar logs estruturados em arquivo.
- Criar testes automatizados para funcoes de extracao e validacao.
- Agendar a execucao recorrente com Task Scheduler, cron ou servico em nuvem.
- Criar dashboard simples para acompanhar execucoes e cartoes movimentados.

## Observacao de Seguranca

Nao publique o arquivo `.env` no repositorio. Ele contem credenciais sensiveis de acesso a API do Trello.

## Autor

Projeto em desenvolvimento como solucao pratica de automacao para otimizar um fluxo real de solicitacoes, projetos e execucao dentro do Trello. O proximo passo é sair do log e ir para um site, para uma visualização melhor dos relatorios gerados.
