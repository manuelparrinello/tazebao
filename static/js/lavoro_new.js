const nuovoLavoroApp = Vue.createApp({
  data() {
    return {
      descrizione: "",
      dataInizio: "",
      dataFine: "",
      dataPagamento: "",
      stato: "Da iniziare",
      priorita: "Bassa",
      preventivato: "",
      cliente: document.querySelector("#formLavoro")?.dataset.selectedClienteId || "",
      note: ""
    };
  },

  methods: {

    async submitForm() {
      const form = document.querySelector("#formLavoro");
      const formData = new FormData(form);
      const cliente_id = formData.get("cliente_id");

      formData.append("descrizione", this.descrizione);
      formData.append("data_inizio", this.dataInizio);
      formData.append("data_fine", this.dataFine);
      formData.append("data_pagamento", this.dataPagamento);
      formData.append("cliente_id", cliente_id);
      formData.append("priorita", this.priorita);
      formData.append("stato", this.stato);
      formData.append("preventivato", this.preventivato);
      formData.append("note", this.note);

      try {
        const response = await fetch("/lavori/new", {
          method: "POST",
          body: formData,
          headers: csrfHeaders(),
        });

        const data = await response.json();

        if (!response.ok) {
          const msg = data.error || "Errore improvviso: HTTP " + response.status;
          window.alert(msg);
          return;
        }

        window.alert(data.message || "Lavoro aggiunto con successo");
        window.location.href = "/clienti/" + cliente_id;
      } catch (error) {
        window.alert("Errore durante il salvataggio: " + error.message);
      }
    },
  },
}).mount("#formLavoro");
