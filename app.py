"""
app.py
------
Backend do StockOS em Python (Flask + SQLite).

Este arquivo define as ROTAS da API REST — os endereços (URLs) que o
navegador acessa para ler ou salvar dados no banco.

Como rodar:
  1. pip install -r requirements.txt
  2. python app.py
  3. Abra http://127.0.0.1:5000 no navegador
"""

from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime

import database

app = Flask(__name__)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
# No banco usamos snake_case (min_stock, cost_price). O frontend espera
# camelCase (minStock, costPrice). Estas funções fazem a "tradução".
# ---------------------------------------------------------------------------

def sku_to_dict(row):
    return {
        "id": str(row["id"]),
        "code": row["code"],
        "name": row["name"],
        "category": row["category"],
        "supplier": row["supplier"],
        "unit": row["unit"],
        "costPrice": row["cost_price"],
        "salePrice": row["sale_price"],
        "stock": row["stock"],
        "minStock": row["min_stock"],
        "maxStock": row["max_stock"],
        "batchControlled": bool(row["batch_controlled"]),
        "warehouse": row["warehouse"],
        "monthlySales": row["monthly_sales"],
    }


def movement_to_dict(row):
    return {
        "id": str(row["id"]),
        "date": row["date"],
        "type": row["type"],
        "reason": row["reason"],
        "skuCode": row["sku_code"],
        "skuName": row["sku_name"],
        "quantity": row["quantity"],
        "operator": row["operator"],
        "warehouse": row["warehouse"],
    }


def batch_to_dict(row):
    return {
        "id": str(row["id"]),
        "batchNumber": row["batch_number"],
        "skuCode": row["sku_code"],
        "skuName": row["sku_name"],
        "mfgDate": row["mfg_date"],
        "expDate": row["exp_date"],
        "quantity": row["quantity"],
        "warehouse": row["warehouse"],
    }


# ---------------------------------------------------------------------------
# PÁGINA PRINCIPAL
# ---------------------------------------------------------------------------
# Entrega o index.html que está na pasta "static/".
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ---------------------------------------------------------------------------
# SKUs (produtos) — CRUD completo
# ---------------------------------------------------------------------------
# CRUD = Create (POST), Read (GET), Update (PUT), Delete (DELETE).
# ---------------------------------------------------------------------------

@app.route("/api/skus", methods=["GET", "POST"])
def skus():
    conn = database.get_connection()

    # READ: listar todos os produtos
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM skus ORDER BY id").fetchall()
        conn.close()
        return jsonify([sku_to_dict(r) for r in rows])

    # CREATE: criar um novo produto
    d = request.get_json() or {}
    try:
        cur = conn.execute(
            """
            INSERT INTO skus
              (code, name, category, supplier, unit, cost_price, sale_price,
               stock, min_stock, max_stock, batch_controlled, warehouse, monthly_sales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                d.get("code"), d.get("name"), d.get("category"), d.get("supplier"),
                d.get("unit"), d.get("costPrice"), d.get("salePrice"),
                d.get("stock", 0), d.get("minStock", 0), d.get("maxStock", 0),
                1 if d.get("batchControlled") else 0,
                d.get("warehouse"), d.get("monthlySales", 0),
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM skus WHERE id = ?", (new_id,)).fetchone()
        conn.close()
        return jsonify(sku_to_dict(row)), 201
    except Exception as exc:  # ex.: código SKU duplicado
        conn.close()
        return jsonify({"error": str(exc)}), 400


@app.route("/api/skus/<int:sku_id>", methods=["PUT", "DELETE"])
def sku_detail(sku_id):
    conn = database.get_connection()

    # DELETE: remover um produto
    if request.method == "DELETE":
        conn.execute("DELETE FROM skus WHERE id = ?", (sku_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    # UPDATE: atualizar um produto
    d = request.get_json() or {}
    conn.execute(
        """
        UPDATE skus SET
          code=?, name=?, category=?, supplier=?, unit=?, cost_price=?,
          sale_price=?, stock=?, min_stock=?, max_stock=?, batch_controlled=?,
          warehouse=?, monthly_sales=?
        WHERE id=?
        """,
        (
            d.get("code"), d.get("name"), d.get("category"), d.get("supplier"),
            d.get("unit"), d.get("costPrice"), d.get("salePrice"),
            d.get("stock"), d.get("minStock"), d.get("maxStock"),
            1 if d.get("batchControlled") else 0,
            d.get("warehouse"), d.get("monthlySales"),
            sku_id,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM skus WHERE id = ?", (sku_id,)).fetchone()
    conn.close()
    return jsonify(sku_to_dict(row))


# ---------------------------------------------------------------------------
# MOVIMENTAÇÕES (entradas, saídas e ajustes)
# ---------------------------------------------------------------------------

@app.route("/api/movements", methods=["GET", "POST"])
def movements():
    conn = database.get_connection()

    # READ: listar movimentações (mais recentes primeiro)
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM movements ORDER BY id DESC").fetchall()
        conn.close()
        return jsonify([movement_to_dict(r) for r in rows])

    # CREATE: registrar uma movimentação E atualizar o saldo do SKU
    d = request.get_json() or {}
    mtype = d.get("type")
    sku_code = d.get("skuCode")
    quantity = int(d.get("quantity", 0))
    reason = d.get("reason", "")

    row = conn.execute("SELECT * FROM skus WHERE code = ?", (sku_code,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": f"SKU {sku_code} não encontrado"}), 404

    current = row["stock"]
    # Regra de negócio: não dá para sair mais do que existe em estoque.
    if mtype in ("Saída", "Ajuste") and current < quantity:
        conn.close()
        return jsonify({
            "error": f"Saldo insuficiente para {sku_code}: apenas {current} disponíveis"
        }), 400

    new_stock = current + quantity if mtype == "Entrada" else current - quantity

    conn.execute("UPDATE skus SET stock = ? WHERE code = ?", (new_stock, sku_code))
    conn.execute(
        """
        INSERT INTO movements (date, type, reason, sku_code, sku_name, quantity, operator, warehouse)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            mtype, reason, sku_code, row["name"], quantity,
            d.get("operator", "Rafael Mendes"), row["warehouse"],
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "newStock": new_stock})


# ---------------------------------------------------------------------------
# LOTES (controle de validade / FIFO)
# ---------------------------------------------------------------------------

@app.route("/api/batches", methods=["GET", "POST"])
def batches():
    conn = database.get_connection()

    # READ: listar lotes ordenados por validade (FIFO: o que vence primeiro vem antes)
    if request.method == "GET":
        rows = conn.execute("SELECT * FROM batches ORDER BY exp_date").fetchall()
        conn.close()
        return jsonify([batch_to_dict(r) for r in rows])

    # CREATE: registrar um lote E somar a quantidade ao estoque do SKU
    d = request.get_json() or {}
    sku_code = d.get("skuCode")
    quantity = int(d.get("quantity", 0))

    sku = conn.execute("SELECT * FROM skus WHERE code = ?", (sku_code,)).fetchone()
    if sku is None:
        conn.close()
        return jsonify({"error": f"SKU {sku_code} não encontrado"}), 404

    conn.execute(
        "UPDATE skus SET stock = stock + ?, batch_controlled = 1 WHERE code = ?",
        (quantity, sku_code),
    )
    conn.execute(
        """
        INSERT INTO batches (batch_number, sku_code, sku_name, mfg_date, exp_date, quantity, warehouse)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            d.get("batchNumber"), sku_code, sku["name"],
            d.get("mfgDate"), d.get("expDate"), quantity, sku["warehouse"],
        ),
    )
    conn.execute(
        """
        INSERT INTO movements (date, type, reason, sku_code, sku_name, quantity, operator, warehouse)
        VALUES (?, 'Entrada', ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            f"Entrada Lote {d.get('batchNumber')}", sku_code, sku["name"],
            quantity, d.get("operator", "Rafael Mendes"), sku["warehouse"],
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201


# ---------------------------------------------------------------------------
# PONTO DE ENTRADA
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    database.init_db()
    print("StockOS backend rodando em http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
