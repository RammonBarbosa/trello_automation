# Essa automação move todos os cartões na lista de projetos(Quadro Solicitação) que tem um cartão anexado
# Este cartão anexado tem que está na lista de finalizados no outro quadro(Quadro Projetos)

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES ---
API_KEY = os.getenv('API_KEY')
TOKEN = os.getenv('TOKEN')
LISTA_PROJETO_SOLICITACOES = '6669a662923d4751850ae26a' #id da lista de projetos do quadro de solicitações
LISTA_FINALIZADO_PROJETOS = '66a3cd4cf460377406141493' #id da lista de finalizados do quadro de projetos
LISTA_EXECUCAO = '6669a6666762039572b85c2d' #id da lista de execução do quadro de solicitações

def rodar_automacao_flexivel():
    print("🔍 Iniciando verificação (Basta um anexo pronto)...")
    url_cards = f"https://api.trello.com/1/lists/{LISTA_PROJETO_SOLICITACOES}/cards"
    params = {'key': API_KEY, 'token': TOKEN, 'attachments': 'true'}
    
    response = requests.get(url_cards, params=params)
    
    if response.status_code != 200:
        print(f"❌ O Trello barrou o acesso! Motivo: {response.text}")
        print(f"Chave lida pelo script: {API_KEY}")
        print(f"Token lido pelo script: {TOKEN}")
        return

    solicitacoes = response.json()
    
    # Variável para contar quantos cartões foram movidos com sucesso <---
    cartoes_movidos = 0

    for cartao in solicitacoes:
        anexos_trello = [a for a in cartao.get('attachments', []) if 'trello.com/c/' in a['url']]
        
        if not anexos_trello:
            continue

        pelo_menos_um_finalizado = False
        nome_anexo_pronto = ""

        for anexo in anexos_trello:
            short_id = anexo['url'].split('/')[-2]
            res_vinculado = requests.get(
                f"https://api.trello.com/1/cards/{short_id}",
                params={'key': API_KEY, 'token': TOKEN}
            )
            
            if res_vinculado.status_code == 200:
                dados = res_vinculado.json()
                if dados['idList'] == LISTA_FINALIZADO_PROJETOS:
                    pelo_menos_um_finalizado = True
                    nome_anexo_pronto = dados['name']
                    break # Encontrou um pronto? Já pode parar de olhar os outros anexos deste cartão

        if pelo_menos_um_finalizado:
            print(f"🚀 SUCESSO: O anexo '{nome_anexo_pronto}' foi finalizado. Movendo '{cartao['name']}'...")
            res_move = requests.put(
                f"https://api.trello.com/1/cards/{cartao['id']}",
                params={'key': API_KEY, 'token': TOKEN, 'idList': LISTA_EXECUCAO}
            )
            
            # ---> NOVO: Se o Trello confirmou a movimentação (status 200), soma 1 no contador <---
            if res_move.status_code == 200:
                cartoes_movidos += 1
                
        else:
            print(f"⏳ '{cartao['name']}': Nenhum dos {len(anexos_trello)} anexos está pronto ainda.")

    # Log final de resumo impresso APÓS o término de todo o laço de repetição <---
    print("\n" + "="*50)
    print("🏁 RELATÓRIO FINAL DA AUTOMAÇÃO 🏁")
    print(f"✅ Total de cartões movidos para Execução: {cartoes_movidos}")
    print("="*50 + "\n")

rodar_automacao_flexivel()