const getLavoroByID = Vue.createApp({
  data() {
    return {
      lavoro: {},
      loading: true,
      error: "",
    };
  },
  methods: {
    async loadLavoroData() {
      const root = document.querySelector("#lavoroPage");
      const id = root.dataset.lavoroId;
      const url = `/api/lavori/get/${id}`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore nella richiesta! HTTP" + response.status);
        }
        console.log("Dati JSON ricevuti!");
        const data = await response.json();
        this.lavoro = data;
        console.log(this.lavoro.cliente.nome);
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },

    renderStatusIcon(stato) {
      if (stato == "In attesa") return "bi bi-hourglass-top";
      if (stato == "In corso") return "bi bi-activity";
      if (stato == "Da iniziare") return "bi bi-play";
      if (stato == "Completato") return "bi bi-check-lg";
      return "";
    },

    renderPrioIcon(prio) {
      if (prio == "Alta") return "bi bi-fire";
      if (prio == "Media") return "bi bi-flag-fill";
      if (prio == "Bassa") return "bi bi-cup-hot-fill";
      return "";
    },

    statoColorText(stato) {
      if (stato == "In attesa") return "stato-in-attesa-onlytext";
      if (stato == "In corso") return "stato-in-corso-onlytext";
      if (stato == "Da iniziare") return "stato-da-iniziare-onlytext";
      if (stato == "Completato") return "stato-completato-onlytext";
      return "";
    },

    statoLavoroText(stato) {
      if (stato == "In attesa") return "stato-in-attesa-text";
      if (stato == "In corso") return "stato-in-corso-text";
      if (stato == "Da iniziare") return "stato-da-iniziare-text";
      if (stato == "Completato") return "stato-completato-text";
      return "";
    },

    prioClass(prio) {
      if (prio === "Bassa") return "prio-low";
      if (prio === "Media") return "prio-med";
      if (prio === "Alta") return "prio-high";
      return "";
    },
  },

  mounted() {
    this.loadLavoroData();
  },
  delimiters: ["[[", "]]"],
}).mount("#lavoroPage");
