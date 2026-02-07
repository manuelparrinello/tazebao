const preventivo = Vue.createApp({
  data() {
    return {
      qty: "",
      descrizione: "",
      prezzo: "",
      clienteData: {},
      indirizzo_cliente: "",
      p_iva_cliente: "",
      sdi_cliente: "",
      clienti: [],
      righe: [],
      idRiga: 0,
      indiceRiga: 0,
      loading: true,
      subtotale: 0,
      totali: [],
      clienteSelezionato: "Seleziona cliente",
    };
  },
  methods: {
    async sendForm(e) {
      e.preventDefault();
      const url = `/preventivi/nuovo`;
      const dataToSend_raw = {
        ragsoc: this.clienteData.ragsoc,
        p_iva: this.clienteData.p_iva,
        indirizzo: this.clienteData.indirizzo,
        citta: this.clienteData.citta,
        cap: this.clienteData.cap,
        provincia: this.clienteData.provincia,
        email: this.clienteData.email,
        telefono: this.clienteData.telefono,
        sdi: this.clienteData.sdi,
        pec: this.clienteData.pec,
        righe: this.righe,
      };
      const dataToSend = JSON.stringify(dataToSend_raw);
      const response = await fetch(url, {
        method: "POST",
        body: dataToSend,
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        throw new Error("Errore richiesta: HTTP " + response.status);
      }
      const data = await response.json();
      let target_url = data["target_url"];
      window.open(target_url, `_blank`);
    },

    async loadClienti() {
      const url = `/api/clienti/getall`;
      const response = await fetch(url, {
        method: "get",
        headers: {
          Accept: "application/json",
        },
      });
      if (!response.ok) {
        throw new Error("Errore HTTP:" + response.status);
      }
      const data = await response.json();
      this.clienti = data;
    },

    async loadClienteDataByID(e) {
      e.preventDefault();
      const id = e.target.value;
      const url = `/api/clienti/get/${id}`;

      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore HTML:" + response.status);
        }
        const data = await response.json();
        this.clienteData = data;
      } catch (error) {
        console.log(error.message);
      } finally {
        this.loading = false;
      }
    },

    calcSubtotale() {
      this.totali = [];
      this.subtotale = 0;

      for (const riga of this.righe) {
        const totaleRiga = Number(riga.totaleRiga) || 0;
        this.totali.push(totaleRiga);
        this.subtotale += totaleRiga;
      }
    },

    async addRigaPreventivo(e) {
      e.preventDefault();
      if (this.clienteSelezionato === "Seleziona cliente") {
        window.alert("Seleziona cliente!");
        return;
      }
      console.clear();
      const form = document.querySelector("#formNuovoPreventivo");
      const formData = new FormData(form);
      const qty = Number(formData.get("qty")) || 0;
      const prezzo = Number(formData.get("prezzo")) || 0;
      const descrizione = String(formData.get("descrizione") || "").trim();
      const riga = {
        idRiga: this.idRiga,
        qty: qty,
        descrizione: descrizione,
        prezzo: prezzo,
        totaleRiga:
          Number(formData.get("qty")) * Number(formData.get("prezzo")),
      };
      this.righe.push(riga);
      const dataToSend = {
        ragsoc: this.clienteData.ragsoc,
        p_iva: this.clienteData.p_iva,
        indirizzo: this.clienteData.indirizzo,
        citta: this.clienteData.citta,
        cap: this.clienteData.cap,
        provincia: this.clienteData.provincia,
        email: this.clienteData.email,
        telefono: this.clienteData.telefono,
        sdi: this.clienteData.sdi,
        pec: this.clienteData.pec,
        righe: this.righe,
      };
      console.log(dataToSend);
      this.calcSubtotale();
      console.log(this.subtotale);
      this.idRiga++;
      this.indiceRiga++;
    },
  },
  mounted() {
    this.loadClienti();
  },
  delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");
