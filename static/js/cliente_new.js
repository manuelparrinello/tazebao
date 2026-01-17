const nuovoClienteApp = Vue.createApp({
  data() {
    return {
      nomeCliente: "",
      telefono: "",
      email: "",
      colore: "",
      note: "",
    };
  },
  computed: {
    inizialiNome() {
      if (this.nomeCliente.length) {
        return this.nomeCliente.charAt(0).toUpperCase();
      } else {
        return "-";
      }
    },
  },
  methods: {
    async submitFormNewCliente(e) {
      e.preventDefault();
      // Creazione di un oggetto FormData per inviare i dati del modulo
      const form = document.querySelector("#nuovoCliente");
      const formData = new FormData(form);
      formData.append('nome_cliente', this.nomeCliente);
      formData.append('telefono', this.telefono);
      formData.append('email', this.email);
      formData.append('note', this.note);
      formData.append('colore', this.colore)

      try {
        const response = await fetch(`/clienti/new`, {
          method: 'post',
          body: formData
        })
        if (!response.ok) {
          throw new Error('Errore richiesta! HTTP' + response.status);
        }
      } catch (error) {
        console.error(error);
      } finally {
        window.alert('Cliente aggiunto!');
        window.location.href = '/clienti';
      }
    },
  },
  delimiters: ["[[", "]]"],
}).mount("#formCliente");