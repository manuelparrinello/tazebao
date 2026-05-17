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
  methods: {
    async clickForDeleteCliente(cliente_id) {
      const url = `/clienti/${cliente_id}`;
      if (await erpConfirm('Vuoi davvero cancellare il cliente?')) {
        fetch(url, {
          method: 'delete',
          headers: csrfHeaders(),
        }).then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          alert('Cliente eliminato con successo!');
          window.location.href = '/clienti';
        }).catch(error => console.log(error));
      }
    }
  },
  mounted() {
    this.clienti = window.CLIENTI_DATA || [];
    this.loading = false;
  },
  delimiters: ["[[", "]]"],
}).mount("#clientiPage");
