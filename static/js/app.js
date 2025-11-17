const app = Vue.createApp({
  data() {
    return {
      nomeCliente: "",
      ragioneSociale: "",
      telefono: "",
      email: "",
      color: "",
      note: "",
    };
  },
  methods: {
    submitForm() {
      // Creazione di un oggetto FormData per inviare i dati del modulo
      const formData = new FormData("#formCliente");
      formData.append("nomeCliente", this.nomeCliente);
      formData.append("ragioneSociale", this.ragioneSociale);
      formData.append("telefono", this.telefono);
      formData.append("email", this.email);
      formData.append("color", this.color);
      formData.append("note", this.note);

      // Invio della richiesta POST al server
      fetch("/cliente/new", {
        method: "POST",
        body: formData,
      }).then((response) => {
        if (response.ok) {
          // Reindirizzamento alla pagina dei clienti dopo il successo
          window.location.href = "/clienti";
        } else {
          console.error("Errore durante la creazione del cliente.");
        }
      });
    },
  },
  delimiters: ["[[", "]]"],
}).mount("#cliente");
