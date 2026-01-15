const getAllLavori = Vue.createApp({
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
        /* setTimeout(() => {
          this.loading = false;
        }, 200000); */
        this.loading = false;
        Vue.nextTick(() => {
          var sorttable_table = document.getElementById("tabellaLavori");
          if (sorttable_table && typeof sorttable !== "undefined") {
            sorttable.makeSortable(sorttable_table);
          }
        });
      }
    },

    prioClass(prio) {
      if (prio === "Bassa") return "prio-low";
      if (prio === "Media") return "prio-med";
      if (prio === "Alta") return "prio-high";
      return "";
    },
  },
  mounted() {
    this.loadLavori();
  },
  delimiters: ["[[", "]]"],
}).mount("#lavoriPage");
