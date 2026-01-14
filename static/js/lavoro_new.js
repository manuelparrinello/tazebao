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
    };
  },
  methods: {
    submitForm(e) {
      e.preventDefault();
      const form = document.querySelector("#nuovoLavoro");
      const formData = new FormData(form);
      formData.append("descrizione", this.descrizione);
      formData.append("dataInizio", this.dataInizio);
      formData.append("dataFine", this.dataFine);
      formData.append("dataPagamento", this.dataPagamento);
      formData.append("stato", this.stato);
      formData.append("priorita", this.priorita);
      formData.append("preventivato", this.preventivato);
      formData.append("cliente", this.cliente);
      fetch("/lavori/new", {
        method: "POST",
        body: formData,
      }).then((response) => {
        if (response.ok) {
          window.alert("Lavoro creato con successo!");
          window.location.href = "/lavori";
        } else {
          console.error("Errore durante la creazione del lavoro.");
        }
      });
    },
  },
}).mount("#formLavoro");