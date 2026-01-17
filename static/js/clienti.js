const getAllClienti = Vue.createApp({
  components: {
    'tabella-clienti': TabellaClienti
  },
  data() {
    return {
      clienti: [],
      loading: true,
      error: null,
      deletingID: null,
    };
  },
  methods: {
    async loadClienti() {
      const url = `/api/clienti/getall`;

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
        this.clienti = await response.json();
      } catch (errore) {
        this.error = errore.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },

    async clickForDeleteCliente(cliente_id) {
      const url = `/clienti/${cliente_id}`;
      if (window.confirm('Vuoi davvero cancellare il cliente?')) {
        try {
          const response = await fetch(url, {
            method: 'delete'
          })
          if (!response.ok) {
            throw new Error(`Errore richiesta! HTTP(${response.status})`)
          }
          alert('Cliente eliminato con successo!');
          window.location.href = '/clienti';
        } catch (error) {
          console.log(error)
        }
      }
      return
    }
  },
  mounted() {
    this.loadClienti();
    console.log(this.loadClienti());
  },
  delimiters: ["[[", "]]"],
}).mount("#clientiPage");