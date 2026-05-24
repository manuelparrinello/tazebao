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
        const resp = await response.json();
        this.cliente = resp.data || {};
        console.log(this.cliente.count_lavori);
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },
    
    async clickForDeleteCliente(event, idCliente) {
      event.preventDefault();
      if (!await erpConfirm("Sei sicuro di voler cancellare il cliente?")) {
        return;
      }

      try {
        const response = await deleteCliente(idCliente);
        console.log("DELETE status:", response.status);
        if (response.ok === false) {
          const corpoRispostaComeTesto = await response.text();
          console.error("Errore response:", corpoRispostaComeTesto);
          throw new Error(
            `Errore durante l'eliminazione (HTTP ${response.status})`
          );
        }
        alert("Cliente eliminato con successo!");
        window.location.href = "/clienti";
      } catch (errore) {
        alert(errore.message);
        console.error(errore);
      }
    },
    async editCliente(e, cliente_id) {
      e.preventDefault();
      const form = document.querySelector("#editClienteForm");
      const formData = new FormData(form);
      function safeVal(v) {
        if (v === undefined || v === null || v === "undefined" || v === "null") return "";
        return v;
      }
      formData.set("nomeCliente", safeVal(this.cliente.nome));
      formData.set("ragsoc", safeVal(this.cliente.ragsoc));
      formData.set("telefono", safeVal(this.cliente.telefono));
      formData.set("email", safeVal(this.cliente.email));
      formData.set("indirizzo", safeVal(this.cliente.indirizzo));
      formData.set("cap", safeVal(this.cliente.cap));
      formData.set("citta", safeVal(this.cliente.citta));
      formData.set("provincia", safeVal(this.cliente.provincia));
      formData.set("p_iva", safeVal(this.cliente.p_iva));
      formData.set("sdi", safeVal(this.cliente.sdi));
      formData.set("pec", safeVal(this.cliente.pec));
      formData.set("note", safeVal(this.cliente.note));
      formData.set("colore", safeVal(this.cliente.colore));

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
            ...csrfHeaders(),
          },
        });
        if (!response.ok) {
          throw new Error(`Errore nella richiesta: HTTP ${response.status} `);
        }
        const data = await response.json();
        window.alert(data.messaggio || `Cliente ${this.cliente.nome} aggiornato con successo!`);
        window.location.href = "/clienti";
      } catch (error) {
        console.error(error);
        window.alert("Errore durante il salvataggio: " + (error.message || "errore sconosciuto"));
      }
    },
  },
  mounted() {
    this.loadClienteData();
    console.log(this.loadClienteData());
  },
  delimiters: ["[[", "]]"],
}).mount("#clienteEditPage");
