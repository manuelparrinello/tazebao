const preventivi = Vue.createApp({
  data() {
    return {
      preventivi: [],
    };
  },
  methods: {
    async fetchAllPreventivi() {
      const url = `/api/preventivi/getall`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore HTTP:" + response.status);
        }
        const data = await response.json();
        for (const preventivo of data) {
          preventivo.data_creazione = new Date(preventivo.data_creazione,
          ).toLocaleDateString("it-IT", {
            day: "numeric",
            month: "long",
            year: "numeric",
          });
        }
        // console.log(data);
        this.preventivi = data;
        console.log(this.preventivi);
      } catch (err) {
        console.log(err);
      }
    },
  },
  delimiters: ["[[", "]]"],
  mounted() {
    this.fetchAllPreventivi();
  },
}).mount("#preventivi");
