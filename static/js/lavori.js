const getAllLavori = Vue.createApp({
  components: {
    'tabella-lavori': TabellaLavori // Registri il componente
  },
  data() {
    return {
      lavori: [],
      loading: true,
      error: null,
      deletingID: null,
    };
  },
  methods: {
    async loadLavori() {
      const url = `/api/lavori/getall`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response) {
          throw new error();
        }
        this.lavori = await response.json();
      } catch (errore) {
        this.error = errore.message || "Errore imprevisto";
      } finally {
        this.loading = false;
        Vue.nextTick(() => {
          var sorttable_table = document.getElementById("tabellaLavori");
          if (sorttable_table && typeof sorttable !== "undefined") {
            sorttable.makeSortable(sorttable_table);
          }
        });
      }
    },

    updateStatus(id) {
      const select = document.querySelector(`#status_select_${id}`);
      const select_value = select.value;
      const url = `/lavori/${id}`;
      console.log(select_value);
      console.log(url);
    }

  },
  mounted() {
    this.loadLavori();
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
}).mount("#lavoriPage");
