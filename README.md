# Sistema de Pagamentos - Trabalho 2

Implementação completa em Python de uma API REST para sistema de vendas/pagamentos, cobrindo os requisitos do trabalho e com extras de arquitetura/documentação.

## Stack
- Python 3.11+
- Flask
- SQLite (nativo)
- Mensageria assíncrona interna com `queue.Queue` + `threading`

## Como rodar
1. Criar ambiente virtual:
```bash
python -m venv .venv
.venv\\Scripts\\activate
```

2. Instalar dependências:
```bash
pip install -r requirements.txt
```

3. Iniciar aplicação:
```bash
python main.py
```

4. API disponível em:
- `http://127.0.0.1:5000`

## Modelo de dados (expandido)
Entidades base pedidas:
- `customers` (cliente)
- `products` (produto)
- `payment_conditions` (condição de pagamento)

Entidades adicionadas:
- `customer_prices` (política/tabela de preços por cliente)
- `sales` (venda)
- `sale_items` (itens da venda)
- `price_drop_notifications` (notificações de queda de preço)

## Endpoints
Base: `/api`

### Health
- `GET /` - status da aplicação

### Clientes
- `POST /api/customers`
- `GET /api/customers`
- `PUT /api/customers/{id}`
- `DELETE /api/customers/{id}`

### Produtos
- `POST /api/products`
- `GET /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`

### Condições de pagamento
- `POST /api/payment-conditions`
- `GET /api/payment-conditions`
- `PUT /api/payment-conditions/{id}`
- `DELETE /api/payment-conditions/{id}`

### Preços por cliente (tabela de preços)
- `POST /api/customer-prices`
- `GET /api/customer-prices`
- `PUT /api/customer-prices/{id}`
- `DELETE /api/customer-prices/{id}`

### Vendas
- `POST /api/sales`
- `GET /api/sales`

### Notificações de queda de preço
- `GET /api/notifications`

### Relatório por cliente
- `GET /api/reports/customer-sales?cnpj=...`
- `GET /api/reports/customer-sales?legal_name=...`

Retorno: vendas e produtos do cliente + consolidado de quantidades e valor total.

## Regra de notificação assíncrona
Quando o preço de um produto é alterado para baixo (`PUT /api/products/{id}`):
1. A API publica evento de mudança em uma fila interna.
2. Worker em background processa sem bloquear a requisição.
3. Para cada item vendido anteriormente com preço maior, gera notificação em `price_drop_notifications`.

Assim, a notificação não depende de requisição HTTP extra e não impacta o tempo de resposta principal.

## Checklist de atendimento ao enunciado
1. Alterar diagrama com novas entidades e relacionamentos:
- Atendido (`customer_prices`, `sales`, `sale_items`, `price_drop_notifications`).

2. CRUD completo do novo modelo:
- Atendido para clientes, produtos, condições de pagamento e tabela de preços.

3. Cadastro de preços para aplicação web:
- Atendido (`/api/customer-prices`).

4. Notificação por mudança de preço de produto já comprado:
- Atendido com processamento assíncrono.

5. Sem degradar performance e sem HTTP para notificação:
- Atendido via fila em memória + worker.

6. Relatório por CNPJ ou Razão Social:
- Atendido (`/api/reports/customer-sales`).

## Extras entregues (além do mínimo)
- Persistência das notificações para auditoria
- Organização por domínio de negócio
- Tratamento de erros básicos (404/400)
- README completo com execução, endpoints e mapeamento do enunciado
