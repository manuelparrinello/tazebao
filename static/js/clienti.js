const getAllClienti = Vue.createApp({
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

    /* editClienti() --> DA FARE QUI SOTTO*/
  },
  mounted() {
    this.loadClienti();
    console.log(this.loadClienti());
  },
  delimiters: ["[[", "]]"],
}).mount("#clientiPage");



// DELETE CLIENTE //
function eliminaCliente(cliente_id) {
        if (!confirm('Sei sicuro di voler eliminare questo cliente?')) return;
        fetch(`/clienti/delete/${cliente_id}`)
            .then(response => response.json())
            .then(msg => {
                alert(msg);
                window.location.href = '/clienti'
            })
    };