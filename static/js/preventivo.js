const preventivo = Vue.createApp({
  data() {
    return {
      titoloProva: "",
      clienti: []
    };
  },
  methods: {
    async sendForm(e) {
      e.preventDefault();
      const url = `/preventivi/nuovo`;
      const form = document.querySelector("#formNuovoPreventivo");
      const formData = new FormData(form);
      formData.append("titolo_prova", this.titoloProva);
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error("Errore richiesta: HTTP " + response.status);
      }
      const data = await response.json()
      let target_url = data['target_url'];
      console.log(target_url);
      window.location.href = target_url;
    },

    async loadClienti() {
        const url = `/api/clienti/getall`;
        const response = await fetch(url, {
            method : 'get',
            headers : {
                'Accept' : 'application/json'
            }
        })
        if (!response.ok) {
            throw new Error('Errore HTTP:' + response.status);
        }
        const data = await response.json();
        this.clienti = data;
        for (const cliente of this.clienti ) {
            console.log(cliente['nome'])
        }
    }
  },
  mounted() {
    this.loadClienti();
  },

  delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");
