const getSingleCliente = Vue.createApp({
  components : {
    'tabella-lavori' : TabellaLavori
  },
  data() {
    return {
      cliente: {},
      error: null,
      loading: true,
    };
  },
  methods: {
    async loadClienteData() {
      const root = document.querySelector("#clientePage");
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
        this.cliente = await response.json();
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },
  },
  mounted() {
    this.loadClienteData();
  },
  updated() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    tooltipTriggerList.forEach(el => {
      // Evita doppie inizializzazioni
      if (!bootstrap.Tooltip.getInstance(el)) {
        new bootstrap.Tooltip(el)
      }
    })
  },
  delimiters: ["[[", "]]"],
}).mount("#clientePage");
