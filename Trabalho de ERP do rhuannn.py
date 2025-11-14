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
            status = "BAIXO-Atenção"
        
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

def exibir_menu():
    print("\n--- Sistema ERP de Estoque ------------------")
    print("1. Cadastrar Produto")
    print("2. Movimentação de Estoque")
    print("3. Excluir Produto")
    print("4. Mostrar Relatório Gerencial")
    print("5. Dashboard")
    print("6. Sair do Programa")
    print("--------------------------------------------")
