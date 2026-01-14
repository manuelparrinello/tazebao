const getSingleCliente = Vue.createApp({
  data() {
    return {
      cliente: {},
      error: null,
      loading: true,
    };
  },
  methods: {
    async loadClienteData() {
      const root = document.querySelector("#clienteEditPage");
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
        console.log(this.cliente.count_lavori);
      } catch (error) {
        this.error = error.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },
    editCliente(e, cliente_id) {
      e.preventDefault();
      const form = document.querySelector('#editClienteForm');
      const formData = new FormData(form); 
      formData.append("nomeCliente", this.cliente.nome); 
      formData.append("telefono", this.cliente.telefono); 
      formData.append("email", this.cliente.email); 
      formData.append("note", this.cliente.note); 
      formData.append("colore", this.cliente.colore);
      const url = `/clienti/edit/${cliente_id}`;

      const formDataJSON = {}
      formData.forEach(function(value, key) {
        formDataJSON[key] = value;
      })
      var json = JSON.stringify(formDataJSON);

      console.log(json)
      try {

        // const response = await fetch(url, {
        //   method: 'put',
        //   body: formData,
        // });



      } catch {

      } finally {

      }
    },
  },
  mounted() {
    this.loadClienteData();
    console.log(this.loadClienteData());
  },
  delimiters: ["[[", "]]"],
}).mount("#clienteEditPage");
