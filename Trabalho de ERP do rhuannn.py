import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

def conectar_bd():
    conexao = sqlite3.connect('estoque.db')
    return conexao

def criar_tabela():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            categoria TEXT,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            data_cadastro TEXT,
            data_ultima_saida TEXT
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            data_movimentacao TEXT NOT NULL,
            tipo TEXT NOT NULL, 
            quantidade INTEGER NOT NULL,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        );
    """)
    
    conn.commit()
    conn.close()
    print("Banco de dados e tabelas verificados com sucesso.")

def cadastrar_produto():
    print("\n--- Cadastro de Novo Produto ---")
    
    nome = input("Nome do Produto: ").strip().capitalize()
    categoria = input("Categoria (ex: Eletronicos, Alimentos): ").strip().capitalize()

    try:
        preco = float(input("Preço Unitário (R$): "))
        quantidade = int(input("Quantidade em Estoque: "))
    except ValueError:
        print("Erro: Preço e Quantidade devem ser números validos!")
        return 
    
    data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    conn = conectar_bd()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO produtos (nome, categoria, preco, quantidade, data_cadastro) 
            VALUES (?, ?, ?, ?, ?)
        """, (nome, categoria, preco, quantidade, data_cadastro))
        
        produto_id = cursor.lastrowid
        
        conn.commit()
        print(f"Produto '{nome}' cadastrado com sucesso no banco de dados!")
        
        registrar_movimentacao(produto_id, 'ENTRADA', quantidade)
    
    except sqlite3.IntegrityError:
        print(f"Erro: O produto '{nome}' já está cadastrado.")
    
    finally:
        conn.close()
    
def registrar_movimentacao(produto_id, tipo, quantidade):
    conn = conectar_bd()
    cursor = conn.cursor()
    data_hora_movimentacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO movimentacoes (produto_id, data_movimentacao, tipo, quantidade) 
        VALUES (?, ?, ?, ?)
    """, (produto_id, data_hora_movimentacao, tipo, quantidade))
    
    conn.commit()
    conn.close()

def atualizar_quantidade(id_produto, quantidade_movimentada, data_saida_manual=None):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (id_produto,))
    resultado = cursor.fetchone()

    if resultado is None:
        print(f"Erro: Produto com ID {id_produto} não encontrado.")
        conn.close()
        return False

    nova_quantidade = resultado[0] + quantidade_movimentada
    
    if nova_quantidade < 0:
        print("Erro: Saldo insuficiente em estoque.")
        conn.close()
        return False
        
    query = "UPDATE produtos SET quantidade = ?"
    params = [nova_quantidade]
    
    if quantidade_movimentada < 0:
        if data_saida_manual:
             data_saida_final = data_saida_manual + " 00:00:00"
        else:
             data_saida_final = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query += ", data_ultima_saida = ?"
        params.append(data_saida_final)
        
        registrar_movimentacao(id_produto, 'SAIDA', abs(quantidade_movimentada))
        
    elif quantidade_movimentada > 0:
        registrar_movimentacao(id_produto, 'ENTRADA', quantidade_movimentada)
        
    query += " WHERE id = ?"
    params.append(id_produto)
        
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    return True

def entrada_estoque():
    print("\n--- Entrada de Estoque  ---")
    try:
        id_produto = int(input("ID do Produto para entrada: "))
        quantidade = int(input("Quantidade a ser adicionada: "))
    except ValueError:
        print("Erro: ID e Quantidade devem ser números.")
        return
    
    if quantidade <= 0:
        print("Erro: A quantidade de entrada deve ser positiva.")
        return

    if atualizar_quantidade(id_produto, quantidade):
        print(f"Entrada de {quantidade} unidades registrada com sucesso!")

def saida_estoque():
    print("\n--- Saida de Estoque  ---")
    try:
        id_produto = int(input("ID do Produto para saida: "))
        quantidade = int(input("Quantidade a ser subtraida: "))
        data_saida_str = input("Digite a data de saida(ex:2025-11-14): ")
        datetime.strptime(data_saida_str, "%Y-%m-%d")
        
    except ValueError:
        print("Erro: ID, Quantidade devem ser números, ou a data de saida está no formato incorreto (use Ano-Mes-Dia).")
        return
        
    if quantidade <= 0:
        print("Erro: A quantidade de saída deve ser positiva.")
        return

    if atualizar_quantidade(id_produto, -quantidade, data_saida_str):
        print(f"Saída de {quantidade} unidades registrada com sucesso! Data de saída registrada: {data_saida_str}.")

def menu_movimentacao():
    print("\n--- Movimentacao de Estoque ---")
    print("1. Entrada ")
    print("2. Saída ")
    escolha = input("Escolha uma opção (1 ou 2): ")
    
    if escolha == '1':
        entrada_estoque()
    elif escolha == '2':
        saida_estoque()
    else:
        print("Opção inválida.")

def excluir_produto():
    print("\n--- Exclusão de Produto ---")
    
    try:
        id_busca = int(input("Digite o ID do produto que deseja excluir: "))
    except ValueError:
        print("Erro: O ID deve ser um número inteiro.")
        return

    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM produtos WHERE id = ?", (id_busca,))
        produto = cursor.fetchone()
        
        if produto:
            nome_produto = produto[0]
            confirmacao = input(f"Tem certeza que deseja excluir o produto '{nome_produto}' (ID: {id_busca})? (sim/nao): ").lower()
            
            if confirmacao == 'sim':
                cursor.execute("DELETE FROM produtos WHERE id = ?", (id_busca,))
                cursor.execute("DELETE FROM movimentacoes WHERE produto_id = ?", (id_busca,))
                conn.commit()
                print(f"Produto '{nome_produto}' e seu histórico excluídos com sucesso do banco de dados!")
            else:
                print("Exclusão cancelada.")
        else:
            print(f"Produto com ID {id_busca} não encontrado.")

    except Exception as e:
        print(f"Ocorreu um erro ao excluir: {e}")
        
    finally:
        conn.close()
        
def mostrar_relatorio():
    print("\n--- Relatório Gerencial de Estoque ---")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, categoria, preco, quantidade, data_cadastro, data_ultima_saida FROM produtos ORDER BY id")
    produtos = cursor.fetchall()
    conn.close()
    
    total_custo_estoque = 0
    formato_data = "%Y-%m-%d %H:%M:%S"
    
    if not produtos:
        print("O estoque está vazio no banco de dados.")
        return

    print("-" * 105)
    print(f"| {'ID':<3} | {'Nome do Produto':<20} | {'Categoria':<15} | {'Preço':<8} | {'Qtd.':<5} | {'Status':<10} | {'Dias em Estoque (TMR)':<20} |")
    print("-" * 105)

    for p in produtos:
        id, nome, categoria, preco, quantidade, data_cadastro, data_ultima_saida = p
        
        custo_unitario = preco * quantidade
        total_custo_estoque += custo_unitario
        
        status = "OK"
        if quantidade < 5:
            status = "BAIXO-[ALERTA]"
        
        dias_em_estoque_str = "N/A"
        
        if data_cadastro:
            data_inicial = datetime.strptime(data_cadastro, formato_data)
            
            if data_ultima_saida:
                data_final = datetime.strptime(data_ultima_saida, formato_data)
            else:
                data_final = datetime.now() 
            
            diferenca = data_final - data_inicial
            dias_em_estoque_str = str(diferenca.days) + " dias"

        linha = f"| {id:<3} | {nome:<20} | {categoria:<15} | R$ {preco:.2f} | {quantidade:<5} | {status:<10} | {dias_em_estoque_str:<20} |"
        print(linha)

    print("-" * 105)
    print(f"Total de produtos diferentes cadastrados: {len(produtos)}")
    print(f"Custo Total de Estoque (Relatório Gerencial): R$ {total_custo_estoque:.2f}")

def gerar_dashboard_todos():
    print("\n--- Dashboards de Acompanhamento  ---")
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    print("Criando 1/3: Curva ABC (Custos)...")
    cursor.execute("""
        SELECT categoria, SUM(preco * quantidade) as custo_total
        FROM produtos
        GROUP BY categoria
        ORDER BY custo_total DESC
    """)
    dados_abc = cursor.fetchall()
    
    if dados_abc:
        categorias = [d[0] for d in dados_abc]
        custos = [d[1] for d in dados_abc]
        
        plt.figure(figsize=(8, 5))
        plt.bar(categorias, custos, color='#1f77b4', alpha=0.8)
        plt.title('Dashboard 1: Curva ABC (Custo por Categoria)')
        plt.xlabel('Categoria do Produto')
        plt.ylabel('Custo Total em Estoque (R$)')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--')
        plt.tight_layout()
        plt.savefig('dashboard_1_curva_abc_custo.png')
        plt.show()
    else:
        print("  [AVISO] Sem dados de custo para Curva ABC.")

    print("Criando 2/3: Comparação de Quantidade...")
    cursor.execute("""
        SELECT categoria, SUM(quantidade) as quantidade_total
        FROM produtos
        GROUP BY categoria
        ORDER BY quantidade_total DESC
    """)
    dados_qtd = cursor.fetchall()

    if dados_qtd:
        categorias_qtd = [d[0] for d in dados_qtd]
        quantidades = [d[1] for d in dados_qtd]
        
        plt.figure(figsize=(8, 5))
        plt.bar(categorias_qtd, quantidades, color='green', alpha=0.8)
        plt.title('Dashboard 2: Comparação de Quantidade por Categoria')
        plt.xlabel('Categoria do Produto')
        plt.ylabel('Quantidade Total em Estoque')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--')
        plt.tight_layout()
        plt.savefig('dashboard_2_comparacao_quantidade.png')
        plt.show()
    else:
        print("  [AVISO] Sem dados de quantidade para comparação.")

    print("Criando 3/3: Evolução do Estoque ...")
    cursor.execute("SELECT data_movimentacao, tipo, quantidade FROM movimentacoes ORDER BY data_movimentacao")
    movimentacoes = cursor.fetchall()
    conn.close()
    
    if movimentacoes:
        historico_diario = {} 
        formato_data = "%Y-%m-%d %H:%M:%S"
        estoque_atual = 0 
        
        for data_hora_str, tipo, quantidade in movimentacoes:
            data_dia = datetime.strptime(data_hora_str, formato_data).date()
            
            if tipo == 'ENTRADA':
                estoque_atual += quantidade
            else:
                estoque_atual -= quantidade
            
            historico_diario[data_dia] = estoque_atual 

        datas = sorted(historico_diario.keys())
        valores_estoque = [historico_diario[data] for data in datas]
        datas_str = [data.strftime("%Y-%m-%d") for data in datas]

        plt.figure(figsize=(10, 6))
        plt.plot(datas_str, valores_estoque, marker='o', color='purple', linestyle='-')
        plt.title('Dashboard 3: Evolução do Estoque Total ')
        plt.xlabel('Data da Movimentação')
        plt.ylabel('Estoque Total (Unidades)')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='both', linestyle=':')
        plt.tight_layout()
        plt.savefig('dashboard_3_evolucao.png')
        plt.show()
    else:
        print("  [AVISO] Sem histórico de movimentações para Evolução do Estoque.")
        
    print("\nTodos os três Dashboards foram salvos no diretório.")

def exibir_menu():
    print("\n--- sistema ERP de Estoque  ---------------")
    print("1. Cadastrar Produto")
    print("2. Movimentação de Estoque")
    print("3. Excluir Produto")
    print("4. Mostrar Relatório Gerencial")
    print("5. Gerar Dashboards")
    print("6. Sair do Programa")
    print("---------------------------------------------")

def main():
    criar_tabela()

    while True:
        exibir_menu()
        
        try:
            opcao = int(input("Escolha uma opção (1-6): "))
        except ValueError:
            print("Opção inválida! Por favor, digite um número.")
            continue

        if opcao == 1:
            cadastrar_produto()
        elif opcao == 2:
            menu_movimentacao()
        elif opcao == 3:
            excluir_produto()
        elif opcao == 4:
            mostrar_relatorio()
        elif opcao == 5:
            gerar_dashboard_todos()
        elif opcao == 6:
            print("Encerrando o sistema.")
            break
        else:
            print("Opção não existe. Escolha um número de 1 a 6.")


main()
