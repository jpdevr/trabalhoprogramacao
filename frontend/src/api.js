const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("text/html")) {
        throw new Error("A API retornou uma pagina HTML em vez de JSON. Veja o erro do backend.");
      }
      throw new Error("A API retornou uma resposta invalida.");
    }
  }

  if (!response.ok) {
    const message = data?.error || data?.detail || "Erro ao comunicar com a API.";
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join(", ") : message);
  }

  return data;
}

export const api = {
  list: (resource) => request(`/${resource}`),
  create: (resource, payload) =>
    request(`/${resource}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (resource, id, payload) =>
    request(`/${resource}/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  remove: (resource, id) =>
    request(`/${resource}/${id}`, {
      method: "DELETE",
    }),
  report: (params) => request(`/reports/customer-sales?${new URLSearchParams(params)}`),
};
