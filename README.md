#  Automação de Movimentação do Trello 

Um script em Python desenvolvido para automatizar o fluxo de trabalho Kanban no Trello. O processo de atendimento de solicitações abrange desde a fase de projeto até a implantação, envolvendo múltiplos quadros e listas para integrar diferentes setores da equipe. A automação atua monitorando constantemente os cartões: ela verifica a conclusão de subprojetos anexados e move automaticamente o cartão principal para a fila de execução, eliminando tarefas manuais e otimizando o tempo de resposta.

##  Funcionalidades

- Varredura automática de cartões na lista de solicitações.
- Verificação do status de cartões anexados (subprojetos).
- Gatilho inteligente: move o cartão principal assim que *um* dos projetos anexados for concluído.
- Sistema de cadência (`time.sleep`) para evitar bloqueios por excesso de requisições (Rate Limiting) na API do Trello.

##  Tecnologias Utilizadas

- **Python 3**
- **Requests:** Para consumo da API REST do Trello.
- **Python-dotenv:** Para gerenciamento seguro de credenciais e variáveis de ambiente.

##  Configuração e Segurança

Este projeto utiliza variáveis de ambiente para proteger as chaves da API. Para rodar localmente, você precisará criar um arquivo `.env` na raiz do projeto.

1. Renomeie o arquivo `.env.example` para `.env` (se houver) ou crie um novo.
2. Adicione suas credenciais geradas no painel de desenvolvedor do Trello:

TRELLO_API_KEY=sua_api_key_aqui
TRELLO_TOKEN=seu_token_aqui


##  Como Executar na Sua Máquina

1. Clone este repositório:
git clone https://github.com/SeuUsuario/trello_automation.git

2. Acesse a pasta do projeto:
cd trello_automation

3. Instale as dependências necessárias:
pip install -r requirements.txt

4. Execute o script:
python main.py

##  Lógica de Funcionamento

O script faz uma requisição `GET` para listar os cartões de uma lista específica. Em seguida, ele mapeia os links anexados e verifica a qual lista esses anexos pertencem. Se a condição for atendida, um `PUT` é enviado para mover o cartão pai para a próxima etapa do funil.