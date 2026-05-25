import requests
import time
import os
from dotenv import load_dotenv

caminho_env = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(caminho_env)

API_KEY = os.getenv('API_KEY')
TOKEN = os.getenv('TOKEN')

# --- CONFIGURAÇÃO DE LISTAS E QUADROS ---
LISTA_EXECUCAO = '6669a6666762039572b85c2d' # Quadro de Solicitações
LISTA_OBRA_PROJETOS = '66a3cd53fa0cf67309404be0' # Lista "Obra" no Quadro de Projetos

def gerar_relatorio_inteligente():
    print("🔍 Iniciando varredura na Lista de Execução...\n")
    url_cards = f"https://api.trello.com/1/lists/{LISTA_EXECUCAO}/cards"
    params = {'key': API_KEY, 'token': TOKEN, 'attachments': 'true'}
    
    response = requests.get(url_cards, params=params)
    if response.status_code != 200:
        print("❌ Erro ao acessar a lista de Execução.")
        return

    solicitacoes_pai = response.json()
    
    # --- VARIÁVEIS DO RELATÓRIO ---
    total_analisados = len(solicitacoes_pai)
    implantacoes_concluidas = 0
    implantacoes_pendentes = 0
    aguardando_obra = 0
    sem_filho_ou_neto = 0
    erros_de_leitura = 0

    print("📋 DETALHAMENTO DOS CARTÕES:")
    print("-" * 80)

    for cartao_pai in solicitacoes_pai:
        nome_pai = cartao_pai['name']
        anexos_pai = [a for a in cartao_pai.get('attachments', []) if 'trello.com/c/' in a['url']]
        
        if not anexos_pai:
            sem_filho_ou_neto += 1
            print(f"⚠️  [SEM PROJETO ANEXADO]  {nome_pai}")
            continue

        short_id_filho = anexos_pai[0]['url'].split('/')[-2]
        
        # BUSCA O FILHO (Projeto)
        res_filho = requests.get(
            f"https://api.trello.com/1/cards/{short_id_filho}",
            params={'key': API_KEY, 'token': TOKEN, 'attachments': 'true'}
        )
        time.sleep(0.2) 
        
        if res_filho.status_code == 200:
            dados_filho = res_filho.json()
            
            # 🏗️ REGRA 1: Se o Filho estiver na lista "Obra", não precisa nem buscar o Neto!
            if dados_filho.get('idList') == LISTA_OBRA_PROJETOS:
                aguardando_obra += 1
                print(f"🏗️  [AGUARDANDO OBRA]      {nome_pai}")
                continue
            
            anexos_filho = [a for a in dados_filho.get('attachments', []) if 'trello.com/c/' in a['url']]
            
            if not anexos_filho:
                sem_filho_ou_neto += 1
                print(f"⚠️  [SEM IMPLANTAÇÃO]      {nome_pai}")
                continue
                
            short_id_neto = anexos_filho[0]['url'].split('/')[-2]
            
            # BUSCA O NETO (Implantação)
            res_neto = requests.get(
                f"https://api.trello.com/1/cards/{short_id_neto}",
                params={'key': API_KEY, 'token': TOKEN}
            )
            time.sleep(0.2) 
            
            if res_neto.status_code == 200:
                dados_neto = res_neto.json()
                
                # Coleta as etiquetas do cartão Neto
                etiquetas_neto = [l['name'].lower() for l in dados_neto.get('labels', [])]
                
                # 🔍 REGRA 2: Verifica se está concluído pela data OU pela etiqueta "vistoriado"
                tem_etiqueta_vistoriado = "VISTORIADO" in etiquetas_neto
                data_concluida = dados_neto.get('dueComplete') == True
                
                if data_concluida or tem_etiqueta_vistoriado:
                    implantacoes_concluidas += 1
                    status_motivo = "Vistoriado" if tem_etiqueta_vistoriado else "Data OK"
                    print(f"✅ [CONCLUÍDO - {status_motivo}]   {nome_pai}")
                else:
                    implantacoes_pendentes += 1
                    print(f"⏳ [PENDENTE]             {nome_pai}")
            
            else:
                erros_de_leitura += 1
                print(f"🚫 [ERRO {res_neto.status_code} NO NETO]      {nome_pai}")
                
        else:
            erros_de_leitura += 1
            print(f"🚫 [ERRO {res_filho.status_code} NO FILHO]     {nome_pai}")

    # --- EXIBIÇÃO DO RELATÓRIO FINAL ---
    print("\n" + "="*50)
    print("📊 RELATÓRIO DE STATUS DA EXECUÇÃO 📊")
    print("="*50)
    print(f"Total de Solicitações na lista:  {total_analisados}")
    print("-" * 50)
    print(f"✅ Implantações CONCLUÍDAS:       {implantacoes_concluidas}")
    print(f"🏗️  Aguardando OBRA:               {aguardando_obra}")
    print(f"⏳ Implantações PENDENTES:        {implantacoes_pendentes}")
    print(f"⚠️  Cartões sem anexo:             {sem_filho_ou_neto}")
    print(f"🚫 Erros de leitura da API:       {erros_de_leitura}")
    print("="*50)
    
    total_somado = implantacoes_concluidas + aguardando_obra + implantacoes_pendentes + sem_filho_ou_neto + erros_de_leitura
    print(f"🔎 Validação Matemática: Soma = {total_somado} (Deve ser igual a {total_analisados})")
    print("="*50 + "\n")

if __name__ == "__main__":
    gerar_relatorio_inteligente()