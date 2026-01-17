const nuovoLavoroApp = Vue.createApp({
  data() {
    return {
      descrizione: "",
      dataInizio: "",
      dataFine: "",
      dataPagamento: "",
      stato: "",
      priorita: "",
      preventivato: "",
      cliente: "",
      note: ""
    };
  },

  methods: {

    async submitForm() {
      const form = document.querySelector("#nuovoLavoro");
      const formData = new FormData(form);
      const cliente_id = formData.get('cliente_id');
      formData.append("descrizione", this.descrizione);
      formData.append("data_inizio", this.dataInizio)
      formData.append("data_fine", this.dataFine)
      formData.append("data_pagamento", this.dataPagamento)
      formData.append("cliente_id", cliente_id)
      formData.append("data_pagamento", this.dataPagamento)
      formData.append("priorita", this.priorita)
      formData.append("stato", this.stato)
      formData.append("preventivato", this.preventivato)
      formData.append("note", this.note)

      try {
        const response = await fetch("/lavori/new", {
          method: "POST",
          body: formData,
        })
        if (!response.ok) {
          throw new Error('Errore improvviso: HTTP' + response.status);
        }
        window.alert("Lavoro aggiunto con successo")
        window.location.href = `/clienti/${cliente_id}`
      } catch (error) {
        console.log(error.message);
      }
    },
  },
}).mount("#formLavoro");