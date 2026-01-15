const getSingleCliente = Vue.createApp({
  data() {
    return {
      cliente: {},
      error: null,
      loading: true,
    };
  },
  methods: {
    async loadClienteData() {
      const root = document.querySelector("#clienteEditPage");
      const cliente_id = root.dataset.clienteId;
      const url = `/api/clienti/get/${cliente_id}`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error(`Errore richiesta! (HTTP ${response.status})`);
        }
        this.cliente = await response.json();
        console.log(this.cliente.count_lavori);
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },
    async editCliente(e, cliente_id) {
      e.preventDefault();
      const form = document.querySelector("#editClienteForm");
      const formData = new FormData(form);
      formData.append("nomeCliente", this.cliente.nome);
      formData.append("telefono", this.cliente.telefono);
      formData.append("email", this.cliente.email);
      formData.append("note", this.cliente.note);
      formData.append("colore", this.cliente.colore);

      const formDataJSON = {};
      formData.forEach(function (value, key) {
        formDataJSON[key] = value;
      });
      var datiClienteJSON = JSON.stringify(formDataJSON);

      console.log(datiClienteJSON);
      try {
        const url = `/clienti/edit/${cliente_id}`;
        const response = await fetch(url, {
          method: "put",
          body: datiClienteJSON,
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
        });
        if (!response.ok) {
          throw new Error(`Errore nella richiesta: HTTP ${response.status} `);
        }
        const data = await response.json();
        console.log(data["messaggio"]);
        window.alert(`Cliente ${this.cliente.nome} aggiornato con successo!`);
        window.location.href = "/clienti";
      } catch {
      } finally {
      }
    },
  },
  mounted() {
    this.loadClienteData();
    console.log(this.loadClienteData());
  },
  delimiters: ["[[", "]]"],
}).mount("#clienteEditPage");
