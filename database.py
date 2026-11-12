"""
database.py
------------
Tudo que envolve o banco de dados SQLite fica aqui:
  - a conexão
  - a criação das tabelas
  - os dados de exemplo (seed) para o painel já abrir preenchido

SQLite é um banco de dados que fica em um único arquivo (stockos.db).
Não precisa instalar nada: ele já vem embutido no Python.
"""

import os
import sqlite3

# O arquivo do banco ficará salvo na mesma pasta deste script.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockos.db")


def get_connection():
    """Abre uma conexão e configura as linhas para serem acessadas por nome.

    Sem o `row_factory = sqlite3.Row`, você acessa uma coluna pelo índice
    (row[0], row[1]...). Com ele, acessa pelo nome (row["name"]), que é
    muito mais legível.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas (se não existirem) e insere dados de exemplo (se vazio).

    Como usamos `CREATE TABLE IF NOT EXISTS` e só inserimos quando a tabela
    está vazia, essa função pode ser chamada toda vez que o servidor sobe,
    sem duplicar dados.
    """
    conn = get_connection()
    cur = conn.cursor()

    # snake_case no banco: min_stock, cost_price, batch_controlled...
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS skus (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            code             TEXT UNIQUE NOT NULL,
            name             TEXT NOT NULL,
            category         TEXT,
            supplier         TEXT,
            unit             TEXT,
            cost_price       REAL,
            sale_price       REAL,
            stock            INTEGER DEFAULT 0,
            min_stock        INTEGER DEFAULT 0,
            max_stock        INTEGER DEFAULT 0,
            batch_controlled INTEGER DEFAULT 0,
            warehouse        TEXT,
            monthly_sales    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS movements (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT,
            type      TEXT,
            reason    TEXT,
            sku_code  TEXT,
            sku_name  TEXT,
            quantity  INTEGER,
            operator  TEXT,
            warehouse TEXT
        );

        CREATE TABLE IF NOT EXISTS batches (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number TEXT,
            sku_code     TEXT,
            sku_name     TEXT,
            mfg_date     TEXT,
            exp_date     TEXT,
            quantity     INTEGER,
            warehouse    TEXT
        );
        """
    )

    cur.execute("SELECT COUNT(*) FROM skus")
    if cur.fetchone()[0] == 0:
        _seed(cur)

    conn.commit()
    conn.close()


def _seed(cur):
    """Insere os mesmos dados de demonstração que o frontend já usava."""

    # code, name, category, supplier, unit, cost, sale, stock, min, max, lote?, warehouse, vendas/mês
    skus = [
        ("EL-NB-014", 'Notebook Corporativo Pro 14"', "Eletrônicos", "TechBrasil Distribuidora",
         "UN", 3450.00, 4890.00, 24, 15, 50, 0, "Depósito Principal", 38),
        ("IN-CF-002", "Café Torrado Especial 1kg", "Alimentos & Insumos", "Torrefação Serra Alta",
         "PCT", 38.50, 64.90, 9, 25, 100, 1, "Depósito Principal", 142),
        ("EL-MN-027", 'Monitor IPS 27" QHD 144Hz', "Eletrônicos", "VisionDisplay Ltda",
         "UN", 1180.00, 1790.00, 46, 10, 35, 0, "Depósito Principal", 21),
        ("CS-SR-088", "Sérum Facial Hidratante 30ml", "Cosméticos", "BioDerma Lab",
         "FR", 29.00, 79.90, 68, 30, 120, 1, "Depósito Principal", 95),
        ("PR-CL-019", "Cadeira Ergonômica Mesh Black", "Mobiliário", "ConfortOffice Ind.",
         "UN", 620.00, 1090.00, 6, 12, 40, 0, "CD São Paulo", 27),
        ("IN-LT-045", "Leite Vegetal Amêndoas 1L", "Alimentos & Insumos", "NaturaVerde Alimentos",
         "CX", 11.20, 19.90, 115, 40, 90, 1, "Depósito Principal", 180),
        ("EL-HD-092", "SSD NVMe 1TB Gen4 Alta Velocidade", "Eletrônicos", "TechBrasil Distribuidora",
         "UN", 310.00, 529.00, 34, 20, 80, 0, "Depósito Principal", 64),
        ("CS-PR-011", "Protetor Solar FPS 60 Toque Seco", "Cosméticos", "BioDerma Lab",
         "UN", 24.50, 58.00, 14, 20, 75, 1, "Filial Sul", 83),
    ]
    cur.executemany(
        """
        INSERT INTO skus
          (code, name, category, supplier, unit, cost_price, sale_price,
           stock, min_stock, max_stock, batch_controlled, warehouse, monthly_sales)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        skus,
    )

    # batch_number, sku_code, sku_name, mfg_date, exp_date, quantity, warehouse
    batches = [
        ("L26-CF-881", "IN-CF-002", "Café Torrado Especial 1kg",
         "2026-06-15", "2026-11-22", 9, "Depósito Principal"),
        ("L26-LT-104", "IN-LT-045", "Leite Vegetal Amêndoas 1L",
         "2026-05-01", "2026-11-08", 18, "Depósito Principal"),
        ("L26-LT-209", "IN-LT-045", "Leite Vegetal Amêndoas 1L",
         "2026-09-10", "2027-03-10", 97, "Depósito Principal"),
        ("L26-SR-412", "CS-SR-088", "Sérum Facial Hidratante 30ml",
         "2026-04-20", "2026-12-05", 28, "Depósito Principal"),
        ("L26-SR-519", "CS-SR-088", "Sérum Facial Hidratante 30ml",
         "2026-08-12", "2027-08-12", 40, "Depósito Principal"),
        ("L26-PR-301", "CS-PR-011", "Protetor Solar FPS 60 Toque Seco",
         "2026-07-01", "2027-06-30", 14, "Filial Sul"),
    ]
    cur.executemany(
        """
        INSERT INTO batches
          (batch_number, sku_code, sku_name, mfg_date, exp_date, quantity, warehouse)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        batches,
    )

    # date, type, reason, sku_code, sku_name, quantity, operator, warehouse
    movements = [
        ("12/11/2026 09:32", "Entrada", "Compra Fornecedor (NF 4821)", "EL-NB-014",
         'Notebook Corporativo Pro 14"', 10, "Rafael Mendes", "Depósito Principal"),
        ("12/11/2026 08:45", "Saída", "Pedido de Venda #3910", "IN-CF-002",
         "Café Torrado Especial 1kg", 16, "Camila Rocha", "Depósito Principal"),
        ("11/11/2026 17:15", "Saída", "Pedido de Venda #3904", "EL-HD-092",
         "SSD NVMe 1TB Gen4 Alta Velocidade", 12, "Rafael Mendes", "Depósito Principal"),
        ("11/11/2026 14:20", "Entrada", "Reposição Estoque (NF 4799)", "IN-LT-045",
         "Leite Vegetal Amêndoas 1L", 50, "Lucas Almeida", "Depósito Principal"),
        ("10/11/2026 16:05", "Ajuste", "Avaria em Transporte (-2 un)", "PR-CL-019",
         "Cadeira Ergonômica Mesh Black", 2, "Rafael Mendes", "CD São Paulo"),
        ("10/11/2026 11:10", "Saída", "Pedido de Venda #3892", "CS-SR-088",
         "Sérum Facial Hidratante 30ml", 22, "Camila Rocha", "Depósito Principal"),
    ]
    cur.executemany(
        """
        INSERT INTO movements
          (date, type, reason, sku_code, sku_name, quantity, operator, warehouse)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        movements,
    )
