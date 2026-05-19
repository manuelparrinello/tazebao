const getAllClienti = Vue.createApp({
  components: {
    'tabella-clienti': TabellaClienti
  },
  data() {
    return {
      clienti: [],
      loading: true,
    };
  },
  mounted() {
    this.clienti = window.CLIENTI_DATA || [];
    this.loading = false;
  },
  delimiters: ["[[", "]]"],
}).mount("#clientiPage");
