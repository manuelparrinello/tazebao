const getSingleCliente = Vue.createApp({
  data() {
    return {
      cliente: {},
      error: null,
      loading: true
    };
  },
  methods: {
    async loadClienteData() {
      const root = document.querySelector("#clientePage");
      const cliente_id = root.dataset.clienteId;
      const url = `/api/clienti/get/${cliente_id}`;
      console.log(url);
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
        console.log(this.cliente.count_lavori)
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false
      }
    },
  },
  mounted() {
    this.loadClienteData();
    console.log(this.loadClienteData());
  },
  delimiters: ["[[", "]]"]
}).mount('#clientePage');