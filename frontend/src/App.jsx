import {
  AlertTriangle,
  Bell,
  Boxes,
  CreditCard,
  FileBarChart,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Search,
  ShoppingCart,
  Tags,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const resources = {
  customers: "customers",
  products: "products",
  paymentConditions: "payment-conditions",
  customerPrices: "customer-prices",
  sales: "sales",
  notifications: "notifications",
};

const sections = [
  { id: "overview", label: "Painel", icon: FileBarChart },
  { id: "customers", label: "Clientes", icon: Users },
  { id: "products", label: "Produtos", icon: Boxes },
  { id: "payment", label: "Condicoes", icon: CreditCard },
  { id: "prices", label: "Precos", icon: Tags },
  { id: "sales", label: "Vendas", icon: ShoppingCart },
  { id: "notifications", label: "Notificacoes", icon: Bell },
  { id: "report", label: "Relatorio", icon: Search },
];

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

function emptyCustomer() {
  return { legal_name: "", cnpj: "", email: "", is_active: true };
}

function emptyProduct() {
  return { sku: "", name: "", base_price: "", is_active: true };
}

function emptyPayment() {
  return { name: "", installments: 1, interest_rate: 0 };
}

function emptyPrice() {
  return { customer_id: "", product_id: "", price: "" };
}

function App() {
  const [active, setActive] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [paymentConditions, setPaymentConditions] = useState([]);
  const [customerPrices, setCustomerPrices] = useState([]);
  const [sales, setSales] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const loadAll = async () => {
    setLoading(true);
    setError("");
    try {
      const [nextCustomers, nextProducts, nextPayments, nextPrices, nextSales, nextNotifications] =
        await Promise.all([
          api.list(resources.customers),
          api.list(resources.products),
          api.list(resources.paymentConditions),
          api.list(resources.customerPrices),
          api.list(resources.sales),
          api.list(resources.notifications),
        ]);

      setCustomers(nextCustomers);
      setProducts(nextProducts);
      setPaymentConditions(nextPayments);
      setCustomerPrices(nextPrices);
      setSales(nextSales);
      setNotifications(nextNotifications);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const names = useMemo(() => {
    return {
      customer: Object.fromEntries(customers.map((item) => [item.id, item.legal_name])),
      product: Object.fromEntries(products.map((item) => [item.id, item.name])),
      payment: Object.fromEntries(paymentConditions.map((item) => [item.id, item.name])),
    };
  }, [customers, products, paymentConditions]);

  const showSuccess = (text) => {
    setMessage(text);
    window.setTimeout(() => setMessage(""), 2600);
  };

  const runMutation = async (action, successText) => {
    setSaving(true);
    setError("");
    try {
      await action();
      await loadAll();
      showSuccess(successText);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const dashboard = {
    totalSales: sales.reduce((sum, sale) => sum + saleTotal(sale), 0),
    activeCustomers: customers.filter((customer) => Boolean(Number(customer.is_active))).length,
    activeProducts: products.filter((product) => Boolean(Number(product.is_active))).length,
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SP</div>
          <div>
            <strong>Pagamentos</strong>
            <span>API REST visual</span>
          </div>
        </div>

        <nav className="nav">
          {sections.map((item) => {
            const Icon = item.icon;
            return (
              <button
                className={active === item.id ? "nav-item active" : "nav-item"}
                key={item.id}
                onClick={() => setActive(item.id)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Sistema de vendas e politica de precos</p>
            <h1>{sections.find((item) => item.id === active)?.label}</h1>
          </div>
          <button className="icon-button" onClick={loadAll} disabled={loading} title="Atualizar dados">
            {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          </button>
        </header>

        {message && <div className="toast success">{message}</div>}
        {error && (
          <div className="toast danger">
            <AlertTriangle size={18} />
            {error}
          </div>
        )}

        {loading ? (
          <div className="loading">
            <Loader2 className="spin" />
            Carregando dados da API...
          </div>
        ) : (
          <>
            {active === "overview" && (
              <Overview
                dashboard={dashboard}
                customers={customers}
                products={products}
                customerPrices={customerPrices}
                sales={sales}
                notifications={notifications}
                names={names}
              />
            )}
            {active === "customers" && (
              <CustomersScreen
                items={customers}
                saving={saving}
                onSave={(payload, id) =>
                  runMutation(
                    () =>
                      id
                        ? api.update(resources.customers, id, payload)
                        : api.create(resources.customers, payload),
                    id ? "Cliente atualizado." : "Cliente cadastrado.",
                  )
                }
                onDelete={(id) =>
                  runMutation(() => api.remove(resources.customers, id), "Cliente removido.")
                }
              />
            )}
            {active === "products" && (
              <ProductsScreen
                items={products}
                saving={saving}
                onSave={(payload, id) =>
                  runMutation(
                    () =>
                      id
                        ? api.update(resources.products, id, payload)
                        : api.create(resources.products, payload),
                    id ? "Produto atualizado. Se o preco caiu, a notificacao sera processada em segundo plano." : "Produto cadastrado.",
                  )
                }
                onDelete={(id) =>
                  runMutation(() => api.remove(resources.products, id), "Produto removido.")
                }
              />
            )}
            {active === "payment" && (
              <PaymentScreen
                items={paymentConditions}
                saving={saving}
                onSave={(payload, id) =>
                  runMutation(
                    () =>
                      id
                        ? api.update(resources.paymentConditions, id, payload)
                        : api.create(resources.paymentConditions, payload),
                    id ? "Condicao atualizada." : "Condicao cadastrada.",
                  )
                }
                onDelete={(id) =>
                  runMutation(() => api.remove(resources.paymentConditions, id), "Condicao removida.")
                }
              />
            )}
            {active === "prices" && (
              <PricesScreen
                customers={customers}
                products={products}
                items={customerPrices}
                names={names}
                saving={saving}
                onSave={(payload, id) =>
                  runMutation(
                    () =>
                      id
                        ? api.update(resources.customerPrices, id, { price: payload.price })
                        : api.create(resources.customerPrices, payload),
                    id ? "Preco atualizado." : "Preco por cliente cadastrado.",
                  )
                }
                onDelete={(id) =>
                  runMutation(() => api.remove(resources.customerPrices, id), "Preco removido.")
                }
              />
            )}
            {active === "sales" && (
              <SalesScreen
                customers={customers}
                products={products}
                paymentConditions={paymentConditions}
                customerPrices={customerPrices}
                sales={sales}
                names={names}
                saving={saving}
                onCreate={(payload) =>
                  runMutation(() => api.create(resources.sales, payload), "Venda registrada.")
                }
              />
            )}
            {active === "notifications" && (
              <NotificationsScreen notifications={notifications} names={names} onRefresh={loadAll} />
            )}
            {active === "report" && <ReportScreen names={names} />}
          </>
        )}
      </main>
    </div>
  );
}

function Overview({ dashboard, customers, products, customerPrices, sales, notifications, names }) {
  const latestSales = [...sales].slice(-4).reverse();
  const latestNotifications = notifications.slice(0, 4);

  return (
    <section className="stack">
      <div className="metric-grid">
        <Metric label="Clientes ativos" value={dashboard.activeCustomers} detail={`${customers.length} cadastrados`} />
        <Metric label="Produtos ativos" value={dashboard.activeProducts} detail={`${products.length} no catalogo`} />
        <Metric label="Tabelas de preco" value={customerPrices.length} detail="politicas cliente x produto" />
        <Metric label="Total vendido" value={money.format(dashboard.totalSales)} detail={`${sales.length} vendas`} />
      </div>

      <div className="split">
        <section className="panel">
          <div className="panel-title">
            <h2>Ultimas vendas</h2>
          </div>
          <DataTable
            empty="Nenhuma venda registrada."
            columns={["Venda", "Cliente", "Condicao", "Valor"]}
            rows={latestSales.map((sale) => [
              `#${sale.id}`,
              names.customer[sale.customer_id] || `Cliente ${sale.customer_id}`,
              names.payment[sale.payment_condition_id] || `Condicao ${sale.payment_condition_id}`,
              money.format(saleTotal(sale)),
            ])}
          />
        </section>

        <section className="panel">
          <div className="panel-title">
            <h2>Quedas de preco</h2>
          </div>
          <DataTable
            empty="Nenhuma notificacao gerada."
            columns={["Cliente", "Produto", "Novo preco"]}
            rows={latestNotifications.map((item) => [
              names.customer[item.customer_id] || `Cliente ${item.customer_id}`,
              names.product[item.product_id] || `Produto ${item.product_id}`,
              money.format(Number(item.new_price)),
            ])}
          />
        </section>
      </div>
    </section>
  );
}

function CustomersScreen({ items, saving, onSave, onDelete }) {
  const [form, setForm] = useState(emptyCustomer());
  const [editing, setEditing] = useState(null);

  const submit = (event) => {
    event.preventDefault();
    onSave({ ...form, is_active: Boolean(form.is_active) }, editing).then(() => {
      setForm(emptyCustomer());
      setEditing(null);
    });
  };

  return (
    <CrudLayout
      title={editing ? "Editar cliente" : "Novo cliente"}
      form={
        <form className="form-grid" onSubmit={submit}>
          <Field label="Razao social" value={form.legal_name} onChange={(value) => setForm({ ...form, legal_name: value })} required />
          <Field label="CNPJ" value={form.cnpj} onChange={(value) => setForm({ ...form, cnpj: value })} required />
          <Field label="Email" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} required />
          <Toggle label="Ativo" checked={Boolean(form.is_active)} onChange={(value) => setForm({ ...form, is_active: value })} />
          <FormActions saving={saving} editing={editing} onCancel={() => { setForm(emptyCustomer()); setEditing(null); }} />
        </form>
      }
      table={
        <DataTable
          empty="Nenhum cliente cadastrado."
          columns={["ID", "Razao social", "CNPJ", "Email", "Status", "Acoes"]}
          rows={items.map((item) => [
            `#${item.id}`,
            item.legal_name,
            item.cnpj,
            item.email,
            Boolean(Number(item.is_active)) ? "Ativo" : "Inativo",
            <RowActions item={item} onEdit={() => { setEditing(item.id); setForm({ ...item, is_active: Boolean(Number(item.is_active)) }); }} onDelete={onDelete} />,
          ])}
        />
      }
    />
  );
}

function ProductsScreen({ items, saving, onSave, onDelete }) {
  const [form, setForm] = useState(emptyProduct());
  const [editing, setEditing] = useState(null);

  const submit = (event) => {
    event.preventDefault();
    onSave({ ...form, base_price: Number(form.base_price), is_active: Boolean(form.is_active) }, editing).then(() => {
      setForm(emptyProduct());
      setEditing(null);
    });
  };

  return (
    <CrudLayout
      title={editing ? "Editar produto" : "Novo produto"}
      note="Ao reduzir o preco base de um produto ja vendido, a API publica um evento interno e grava notificacoes sem criar uma chamada HTTP adicional."
      form={
        <form className="form-grid" onSubmit={submit}>
          <Field label="SKU" value={form.sku} onChange={(value) => setForm({ ...form, sku: value })} required />
          <Field label="Nome" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
          <Field label="Preco base" type="number" step="0.01" value={form.base_price} onChange={(value) => setForm({ ...form, base_price: value })} required />
          <Toggle label="Ativo" checked={Boolean(form.is_active)} onChange={(value) => setForm({ ...form, is_active: value })} />
          <FormActions saving={saving} editing={editing} onCancel={() => { setForm(emptyProduct()); setEditing(null); }} />
        </form>
      }
      table={
        <DataTable
          empty="Nenhum produto cadastrado."
          columns={["ID", "SKU", "Nome", "Preco base", "Status", "Acoes"]}
          rows={items.map((item) => [
            `#${item.id}`,
            item.sku,
            item.name,
            money.format(Number(item.base_price)),
            Boolean(Number(item.is_active)) ? "Ativo" : "Inativo",
            <RowActions item={item} onEdit={() => { setEditing(item.id); setForm({ ...item, is_active: Boolean(Number(item.is_active)) }); }} onDelete={onDelete} />,
          ])}
        />
      }
    />
  );
}

function PaymentScreen({ items, saving, onSave, onDelete }) {
  const [form, setForm] = useState(emptyPayment());
  const [editing, setEditing] = useState(null);

  const submit = (event) => {
    event.preventDefault();
    onSave(
      {
        name: form.name,
        installments: Number(form.installments),
        interest_rate: Number(form.interest_rate),
      },
      editing,
    ).then(() => {
      setForm(emptyPayment());
      setEditing(null);
    });
  };

  return (
    <CrudLayout
      title={editing ? "Editar condicao" : "Nova condicao"}
      form={
        <form className="form-grid" onSubmit={submit}>
          <Field label="Nome" value={form.name} onChange={(value) => setForm({ ...form, name: value })} required />
          <Field label="Parcelas" type="number" min="1" value={form.installments} onChange={(value) => setForm({ ...form, installments: value })} required />
          <Field label="Juros" type="number" step="0.0001" value={form.interest_rate} onChange={(value) => setForm({ ...form, interest_rate: value })} required />
          <FormActions saving={saving} editing={editing} onCancel={() => { setForm(emptyPayment()); setEditing(null); }} />
        </form>
      }
      table={
        <DataTable
          empty="Nenhuma condicao cadastrada."
          columns={["ID", "Nome", "Parcelas", "Juros", "Acoes"]}
          rows={items.map((item) => [
            `#${item.id}`,
            item.name,
            item.installments,
            `${Number(item.interest_rate)}%`,
            <RowActions item={item} onEdit={() => { setEditing(item.id); setForm(item); }} onDelete={onDelete} />,
          ])}
        />
      }
    />
  );
}

function PricesScreen({ customers, products, items, names, saving, onSave, onDelete }) {
  const [form, setForm] = useState(emptyPrice());
  const [editing, setEditing] = useState(null);
  const [localError, setLocalError] = useState("");

  const submit = (event) => {
    event.preventDefault();
    setLocalError("");

    if (!editing) {
      const duplicate = items.find(
        (item) =>
          Number(item.customer_id) === Number(form.customer_id) &&
          Number(item.product_id) === Number(form.product_id),
      );
      if (duplicate) {
        setLocalError("Ja existe um preco cadastrado para este cliente e produto. Edite o registro existente.");
        return;
      }
    }

    onSave(
      {
        customer_id: Number(form.customer_id),
        product_id: Number(form.product_id),
        price: Number(form.price),
      },
      editing,
    ).then(() => {
      setForm(emptyPrice());
      setEditing(null);
    });
  };

  return (
    <CrudLayout
      title={editing ? "Editar preco" : "Novo preco por cliente"}
      note="Esta tela representa a politica de precos praticados que forma a tabela de precos de cada cliente."
      form={
        <form className="form-grid" onSubmit={submit}>
          <SelectField label="Cliente" value={form.customer_id} onChange={(value) => setForm({ ...form, customer_id: value })} disabled={Boolean(editing)} required>
            <option value="">Selecione</option>
            {customers.map((item) => <option key={item.id} value={item.id}>{item.legal_name}</option>)}
          </SelectField>
          <SelectField label="Produto" value={form.product_id} onChange={(value) => setForm({ ...form, product_id: value })} disabled={Boolean(editing)} required>
            <option value="">Selecione</option>
            {products.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <Field label="Preco negociado" type="number" step="0.01" value={form.price} onChange={(value) => setForm({ ...form, price: value })} required />
          {localError && <div className="inline-error form-inline-error">{localError}</div>}
          <FormActions saving={saving} editing={editing} onCancel={() => { setForm(emptyPrice()); setEditing(null); }} />
        </form>
      }
      table={
        <DataTable
          empty="Nenhuma politica de preco cadastrada."
          columns={["ID", "Cliente", "Produto", "Preco", "Atualizado em", "Acoes"]}
          rows={items.map((item) => [
            `#${item.id}`,
            names.customer[item.customer_id] || `Cliente ${item.customer_id}`,
            names.product[item.product_id] || `Produto ${item.product_id}`,
            money.format(Number(item.price)),
            formatDate(item.updated_at),
            <RowActions item={item} onEdit={() => { setEditing(item.id); setForm(item); }} onDelete={onDelete} />,
          ])}
        />
      }
    />
  );
}

function SalesScreen({ customers, products, paymentConditions, customerPrices, sales, names, saving, onCreate }) {
  const [form, setForm] = useState({
    customer_id: "",
    payment_condition_id: "",
    items: [{ product_id: "", quantity: 1 }],
  });

  const customPriceMap = useMemo(() => {
    return new Map(customerPrices.map((item) => [`${item.customer_id}:${item.product_id}`, Number(item.price)]));
  }, [customerPrices]);

  const effectivePrice = (productId) => {
    if (!productId) return 0;
    const custom = customPriceMap.get(`${form.customer_id}:${productId}`);
    if (custom) return custom;
    return Number(products.find((item) => Number(item.id) === Number(productId))?.base_price || 0);
  };

  const total = form.items.reduce((sum, item) => sum + effectivePrice(item.product_id) * Number(item.quantity || 0), 0);

  const submit = (event) => {
    event.preventDefault();
    onCreate({
      customer_id: Number(form.customer_id),
      payment_condition_id: Number(form.payment_condition_id),
      items: form.items.map((item) => ({
        product_id: Number(item.product_id),
        quantity: Number(item.quantity),
      })),
    }).then(() => {
      setForm({ customer_id: "", payment_condition_id: "", items: [{ product_id: "", quantity: 1 }] });
    });
  };

  return (
    <section className="stack">
      <section className="panel">
        <div className="panel-title">
          <h2>Registrar venda</h2>
          <strong>{money.format(total)}</strong>
        </div>
        <form className="form-grid wide" onSubmit={submit}>
          <SelectField label="Cliente" value={form.customer_id} onChange={(value) => setForm({ ...form, customer_id: value })} required>
            <option value="">Selecione</option>
            {customers.map((item) => <option key={item.id} value={item.id}>{item.legal_name}</option>)}
          </SelectField>
          <SelectField label="Condicao de pagamento" value={form.payment_condition_id} onChange={(value) => setForm({ ...form, payment_condition_id: value })} required>
            <option value="">Selecione</option>
            {paymentConditions.map((item) => <option key={item.id} value={item.id}>{item.name} - {item.installments}x</option>)}
          </SelectField>

          <div className="items-editor">
            {form.items.map((item, index) => (
              <div className="item-row" key={index}>
                <SelectField label="Produto" value={item.product_id} onChange={(value) => {
                  const next = [...form.items];
                  next[index] = { ...item, product_id: value };
                  setForm({ ...form, items: next });
                }} required>
                  <option value="">Selecione</option>
                  {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                </SelectField>
                <Field label="Qtd." type="number" min="1" value={item.quantity} onChange={(value) => {
                  const next = [...form.items];
                  next[index] = { ...item, quantity: value };
                  setForm({ ...form, items: next });
                }} required />
                <div className="price-pill">{money.format(effectivePrice(item.product_id))}</div>
                <button
                  className="icon-button"
                  type="button"
                  onClick={() => setForm({ ...form, items: form.items.filter((_, itemIndex) => itemIndex !== index) })}
                  disabled={form.items.length === 1}
                  title="Remover item"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button
              className="secondary"
              type="button"
              onClick={() => setForm({ ...form, items: [...form.items, { product_id: "", quantity: 1 }] })}
            >
              <Plus size={16} />
              Item
            </button>
            <button className="primary" disabled={saving} type="submit">
              <Save size={16} />
              Salvar venda
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-title">
          <h2>Historico de vendas</h2>
        </div>
        <DataTable
          empty="Nenhuma venda registrada."
          columns={["ID", "Cliente", "Condicao", "Itens", "Total", "Criada em"]}
          rows={sales.map((sale) => [
            `#${sale.id}`,
            names.customer[sale.customer_id] || `Cliente ${sale.customer_id}`,
            names.payment[sale.payment_condition_id] || `Condicao ${sale.payment_condition_id}`,
            sale.items.map((item) => `${names.product[item.product_id] || item.product_id} x${item.quantity}`).join(", "),
            money.format(saleTotal(sale)),
            formatDate(sale.created_at),
          ])}
        />
      </section>
    </section>
  );
}

function NotificationsScreen({ notifications, names, onRefresh }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <h2>Notificacoes de queda de preco</h2>
          <p>Geradas pelo worker interno quando um produto vendido fica mais barato.</p>
        </div>
        <button className="secondary" onClick={onRefresh}>
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>
      <DataTable
        empty="Nenhuma notificacao encontrada."
        columns={["ID", "Cliente", "Produto", "Preco pago", "Novo preco", "Mensagem", "Criada em"]}
        rows={notifications.map((item) => [
          `#${item.id}`,
          names.customer[item.customer_id] || `Cliente ${item.customer_id}`,
          names.product[item.product_id] || `Produto ${item.product_id}`,
          money.format(Number(item.old_price_paid)),
          money.format(Number(item.new_price)),
          item.message,
          formatDate(item.created_at),
        ])}
      />
    </section>
  );
}

function ReportScreen() {
  const [mode, setMode] = useState("cnpj");
  const [query, setQuery] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);
    try {
      setReport(await api.report({ [mode]: query }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="stack">
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>Relatorio por cliente</h2>
            <p>Localize por CNPJ ou por parte da razao social.</p>
          </div>
        </div>
        <form className="search-form" onSubmit={submit}>
          <div className="segmented">
            <button className={mode === "cnpj" ? "active" : ""} type="button" onClick={() => setMode("cnpj")}>CNPJ</button>
            <button className={mode === "legal_name" ? "active" : ""} type="button" onClick={() => setMode("legal_name")}>Razao social</button>
          </div>
          <Field label="Busca" value={query} onChange={setQuery} required />
          <button className="primary" disabled={loading} type="submit">
            {loading ? <Loader2 className="spin" size={16} /> : <Search size={16} />}
            Consultar
          </button>
        </form>
        {error && <div className="inline-error">{error}</div>}
      </section>

      {report && (
        <section className="panel">
          <div className="report-head">
            <div>
              <p className="eyebrow">Cliente #{report.customer_id}</p>
              <h2>{report.legal_name}</h2>
              <span>{report.cnpj}</span>
            </div>
            <div className="report-total">
              <span>Total</span>
              <strong>{money.format(Number(report.total_amount))}</strong>
            </div>
          </div>
          <div className="metric-grid compact">
            <Metric label="Vendas" value={report.sales_count} detail="compras localizadas" />
            <Metric label="Produtos distintos" value={report.products.length} detail="itens consolidados" />
          </div>
          <DataTable
            empty="Cliente localizado, mas sem produtos vendidos."
            columns={["Produto", "Quantidade", "Total"]}
            rows={report.products.map((item) => [
              item.product_name,
              item.quantity,
              money.format(Number(item.total)),
            ])}
          />
        </section>
      )}
    </section>
  );
}

function Metric({ label, value, detail }) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function CrudLayout({ title, note, form, table }) {
  return (
    <section className="stack">
      <section className="panel">
        <div className="panel-title">
          <div>
            <h2>{title}</h2>
            {note && <p>{note}</p>}
          </div>
        </div>
        {form}
      </section>
      <section className="panel">{table}</section>
    </section>
  );
}

function Field({ label, onChange, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input {...props} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function SelectField({ label, children, onChange, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select {...props} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
    </label>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function FormActions({ saving, editing, onCancel }) {
  return (
    <div className="form-actions">
      {editing && (
        <button className="secondary" type="button" onClick={onCancel}>
          <X size={16} />
          Cancelar
        </button>
      )}
      <button className="primary" type="submit" disabled={saving}>
        {saving ? <Loader2 className="spin" size={16} /> : <Save size={16} />}
        {editing ? "Atualizar" : "Cadastrar"}
      </button>
    </div>
  );
}

function RowActions({ item, onEdit, onDelete }) {
  return (
    <div className="row-actions">
      <button className="icon-button" onClick={onEdit} title="Editar">
        <Pencil size={16} />
      </button>
      <button className="icon-button danger" onClick={() => onDelete(item.id)} title="Excluir">
        <Trash2 size={16} />
      </button>
    </div>
  );
}

function DataTable({ columns, rows, empty }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column}>{column}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="empty" colSpan={columns.length}>{empty}</td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr key={index}>
                {row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function saleTotal(sale) {
  return sale.items.reduce((sum, item) => sum + Number(item.unit_price) * Number(item.quantity), 0);
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export default App;
