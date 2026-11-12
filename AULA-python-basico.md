# 🐍 Aula: Python na prática com o seu StockOS

> Você não precisa decorar nada. Esta aula usa o código que **acabamos de criar**
> (`app.py` e `database.py`) para te ensinar os fundamentos de Python.
> Abra os arquivos ao lado e acompanhe.

---

## 1. Variáveis: caixinhas com nome

Uma variável guarda um valor com um nome.

```python
sku_code = "IN-CF-002"      # texto (string)
quantity  = 10              # número inteiro (int)
price     = 38.50           # número decimal (float)
ativo     = True            # verdadeiro/falso (bool)
```

No seu `app.py`, temos exatamente isso:

```python
mtype    = d.get("type")
sku_code = d.get("skuCode")
quantity = int(d.get("quantity", 0))
```

💡 `int(...)` converte para número inteiro, porque do navegador **tudo chega como texto**.

---

## 2. Funções: pedaços de código reutilizáveis

Uma função tem um nome, pode receber dados (parâmetros) e devolver um resultado (`return`).

```python
def formatCurrency(val):
    return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
```

Esse exemplo é JavaScript. Em **Python** a sintaxe é igual em espírito:

```python
def dobro(x):
    return x * 2

dobro(5)   # → 10
```

No seu `database.py`:

```python
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

- `def get_connection():` → define a função
- as linhas indentadas (com espaços na frente) → são o **corpo** da função
- `return conn` → devolve a conexão para quem chamou

⚠️ **A indentação é obrigatória no Python.** É ela que define onde um bloco começa e termina (diferente do `{ }` do JavaScript).

---

## 3. Dicionários: pares chave → valor

É o "objeto" do Python. Muito parecido com o objeto do JavaScript.

```python
sku = {
    "code": "IN-CF-002",
    "name": "Café Torrado Especial 1kg",
    "stock": 9,
    "batchControlled": True,
}
```

Acessamos assim:

```python
sku["name"]        # → "Café Torrado Especial 1kg"
sku.get("name")    # → igual, mas não dá erro se a chave não existir
```

No seu `app.py`, a função `sku_to_dict` **constrói um dicionário** para responder ao navegador:

```python
def sku_to_dict(row):
    return {
        "id": str(row["id"]),
        "code": row["code"],
        "name": row["name"],
        "stock": row["stock"],
        "batchControlled": bool(row["batch_controlled"]),
        # ...
    }
```

Perceba o truque: no banco o campo se chama `min_stock` (snake_case), mas o
frontend espera `minStock` (camelCase). Essa função faz a "tradução".

---

## 4. Listas e o laço `for`

Lista é uma sequência de valores. `for` percorre uma lista item por item.

```python
frutas = ["maçã", "banana", "uva"]

for f in frutas:
    print(f)          # imprime cada fruta
```

No seu `app.py` (rota que lista produtos):

```python
rows = conn.execute("SELECT * FROM skus ORDER BY id").fetchall()
return jsonify([sku_to_dict(r) for r in rows])
```

A linha `[sku_to_dict(r) for r in rows]` é uma **list comprehension**:
"para cada linha `r` em `rows`, transforme com `sku_to_dict` e monte uma lista".

É a mesma coisa que:

```python
resultado = []
for r in rows:
    resultado.append(sku_to_dict(r))
```

---

## 5. Condicionais: `if` / `elif` / `else`

Tomar decisões é a essência de programar.

```python
if estoque == 0:
    status = "Esgotado"
elif estoque < minimo:
    status = "Abaixo do mínimo"
else:
    status = "OK"
```

No seu `app.py`, a regra de negócio mais importante:

```python
if mtype in ("Saída", "Ajuste") and current < quantity:
    return jsonify({"error": f"Saldo insuficiente para {sku_code}..."}), 400

new_stock = current + quantity if mtype == "Entrada" else current - quantity
```

Leia a última linha em português: `new_stock` é `current + quantity` **se** for
"Entrada", **senão** é `current - quantity`. Isso se chama **operador ternário**
(um `if` de uma linha só).

---

## 6. f-strings: texto com variáveis dentro

O `f` antes das aspas permite colocar variáveis dentro da string com `{ }`.

```python
nome = "Café"
print(f"Produto: {nome}")     # → Produto: Café
```

No seu código:

```python
return jsonify({"error": f"SKU {sku_code} não encontrado"}), 404
```

---

## 7. `@app.route(...)`: o "decorador" que cria uma rota

```python
@app.route("/api/skus", methods=["GET", "POST"])
def skus():
    ...
```

Isso significa: "quando alguém acessar `http://127.0.0.1:5000/api/skus`
com GET ou POST, execute a função `skus` abaixo."

- `GET` = o navegador **pede** dados (ler)
- `POST` = o navegador **envia** dados (criar)
- `PUT` = atualizar
- `DELETE` = apagar

O `@` é um **decorator** — ele "envelopa" a função. Por enquanto, entenda
apenas que é assim que o Flask liga uma URL a um código.

---

## 8. SQL básico (o que o `database.py` faz)

SQL é a linguagem para conversar com o banco. As 4 operações principais:

```sql
SELECT * FROM skus;                            -- ler tudo
INSERT INTO skus (...) VALUES (...);           -- criar
UPDATE skus SET stock = 7 WHERE code = 'X';    -- atualizar
DELETE FROM skus WHERE id = 3;                 -- apagar
```

No seu `database.py`, o `cur.executemany(...)` insere vários registros de uma vez:

```python
cur.executemany(
    "INSERT INTO skus (...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    skus,   # ← uma lista de tuplas
)
```

Os `?` são **placeholders**: o banco substitui cada `?` pelos valores da lista,
de forma segura (evita o famoso "SQL injection").

---

## 9. O fluxo completo (resumo do que você construiu)

```
1. Você abre http://127.0.0.1:5000
   ↓
2. Flask serve o index.html (rota "/")
   ↓
3. O JavaScript chama fetch('/api/skus')
   ↓
4. Flask executa a função skus()  →  consulta o SQLite  →  devolve JSON
   ↓
5. O JavaScript desenha o painel com os dados
```

Quando você cadastra uma saída:

```
fetch POST /api/movements  →  Flask valida  →  atualiza o estoque no banco
                           →  responde {ok: true, newStock: 7}
                           →  JavaScript recarrega (loadFromApi)
```

---

## 10. Exercícios (faça para fixar!)

1. **Mude a mensagem de erro** em `app.py`: em vez de "Saldo insuficiente para...",
   escreva "⚠️ Estoque insuficiente do produto X (restam N unidades)". Dica: use f-string.

2. **Adicione um print**: dentro da função `skus()`, adicione `print("Alguém pediu a lista de SKUs")`
   e rode `python app.py`. Veja a mensagem aparecer no terminal cada vez que você recarregar a página.

3. **Crie um SKU novo** pelo próprio painel (aba "Cadastro de SKU" → "+ Novo SKU"),
   depois feche e reabra o navegador. O produto deve continuar lá. Por quê? Porque agora está no banco!

4. **Explique com suas palavras** (pode me mandar aqui no chat): qual a diferença entre
   `GET` e `POST`? Por que o `loadFromApi()` precisa ser `async`?

5. **Desafio**: no `app.py`, a rota `/api/batches` ordena por `exp_date`. Mude para ordenar
   por `quantity` (maior primeiro) e veja a lista de lotes mudar de ordem. Depois volte ao original.

---

Pronto! Você já entende os blocos de construção de **qualquer** programa Python:
variáveis, funções, dicionários, listas, `for`, `if`, strings e agora até SQL.
Tudo isso usando um sistema real que você mesmo montou. 🚀
