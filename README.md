# StockOS — Backend (Python + Flask + SQLite)

## Como rodar

```bash
# 1. (opcional, mas recomendado) criar um ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows

# 2. instalar as dependências
pip install -r requirements.txt

# 3. rodar o servidor
python app.py
```

Depois abra no navegador: **http://127.0.0.1:5000**

## Onde colocar seu HTML

Salve o seu `index.html` completo dentro da pasta `static/`, substituindo o
arquivo de teste. Em seguida, aplique as alterações de integração
(loadData + fetch) descritas na conversa.

## Endpoints da API

| Método | Rota             | O que faz                                  |
|--------|------------------|--------------------------------------------|
| GET    | /api/skus        | Lista todos os produtos                    |
| POST   | /api/skus        | Cria um produto                            |
| PUT    | /api/skus/<id>   | Atualiza um produto                        |
| DELETE | /api/skus/<id>   | Remove um produto                          |
| GET    | /api/movements   | Lista movimentações (mais recentes primeiro) |
| POST   | /api/movements   | Registra movimentação e atualiza o saldo   |
| GET    | /api/batches     | Lista lotes ordenados por validade (FIFO)  |
| POST   | /api/batches     | Registra lote e soma ao estoque            |

## Testar a API sem o navegador

```bash
# listar SKUs
curl http://127.0.0.1:5000/api/skus

# registrar uma saída de 2 unidades do café
curl -X POST http://127.0.0.1:5000/api/movements ^
  -H "Content-Type: application/json" ^
  -d "{\"type\":\"Saída\",\"skuCode\":\"IN-CF-002\",\"quantity\":2,\"reason\":\"Teste\"}"
```
