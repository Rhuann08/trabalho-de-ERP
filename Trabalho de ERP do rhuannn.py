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
        data_saida_str = input("Digite a data de saida (ex:2025-11-14): ")
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

def exibir_menu():
    print("\n--- Mini-ERP de Estoque ------------------")
    print("1. Cadastrar Produto")
    print("2. Movimentação de Estoque")
    print("3. Excluir Produto")
    print("4. Mostrar Relatório Gerencial")
    print("5. Dashboard")
    print("6. Sair do Programa")
    print("--------------------------------------------")
