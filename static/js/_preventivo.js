const _preventivo = Vue.createApp({
  data() {
    return {
      preventivoData: {},
      cliente: {},
      subtotale: 0,
    };
  },
  methods: {
    calcSubtotale() {
        for (const riga of this.preventivoData.righe) {
            const totale = Number(String(riga.totale_riga).replace(",", "."));
            this.subtotale += Number.isFinite(totale) ? totale : 0;
        } 
    },
    async loadPreventivoData() {
      const segments = window.location.pathname.split("/").filter(Boolean);
      const id = segments.at(-1);
      console.log(id);
      const url = `/api/preventivi/get/${id}`;
      console.log(url);
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore: HTML " + response.status);
        }
        const data = await response.json();
        this.preventivoData = data;
        this.cliente = data.cliente;
        this.calcSubtotale()
        console.log("Dati ricevuti");
      } catch (err) {
        console.log(err);
      }
    },
  },
  mounted() {
    this.loadPreventivoData();
    console.log(JSON.stringify(this.preventivoData));
  },
  delimiters: ["[[", "]]"],
}).mount("#preventivoView");
