from duplicates import gerar_relatorio_duplicados
from moveproj import rodar_automacao_flexivel
from readexc import gerar_relatorio_inteligente
from readproj import gerar_relatorio_projetos


def main() -> None:
    opcoes = {
        "1": ("Relatorio de projetos prontos", gerar_relatorio_projetos),
        "2": ("Relatorio da lista de execucao", gerar_relatorio_inteligente),
        "3": ("Relatorio de duplicados", gerar_relatorio_duplicados),
        "4": ("Mover cartoes para execucao", rodar_automacao_flexivel),
    }

    print("Automacao Trello")
    print("-" * 40)
    for codigo, (descricao, _) in opcoes.items():
        print(f"{codigo} - {descricao}")

    escolha = input("\nEscolha uma opcao: ").strip()
    opcao = opcoes.get(escolha)

    if not opcao:
        print("Opcao invalida.")
        return

    descricao, funcao = opcao
    print(f"\nExecutando: {descricao}\n")
    funcao()


if __name__ == "__main__":
    main()
