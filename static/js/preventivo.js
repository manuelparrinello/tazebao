const preventivo = Vue.createApp({
    data() {
        return {
            qty: "",
            descrizione: "",
            prezzo: "",
            clienteData: {},
            indirizzo_cliente: "",
            p_iva_cliente: "",
            sdi_cliente: "",
            clienti: [],
            loading: true,
            righeLavoro: [],
            idRiga: 0,
            addingHasEnded: false,
            indiceRigheLavoro: 0
        };
    },
    methods: {

        async sendForm(e) {
            e.preventDefault();
            const url = `/preventivi/nuovo`;
            const form = document.querySelector("#formNuovoPreventivo");
            const formData = new FormData(form);
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                throw new Error("Errore richiesta: HTTP " + response.status);
            }
            const data = await response.json()
            let target_url = data['target_url'];
            window.open(target_url, `_blank`)
        },

        async loadClienti() {
            const url = `/api/clienti/getall`;
            const response = await fetch(url, {
                method: 'get',
                headers: {
                    'Accept': 'application/json'
                }
            })
            if (!response.ok) {
                throw new Error('Errore HTTP:' + response.status);
            }
            const data = await response.json();
            this.clienti = data;
            for (const cliente of this.clienti) {}
        },

        async loadClienteDataByID(e) {
            const id = e.target.value;
            const url = `/api/clienti/get/${id}`;

            try {
                const response = await fetch(url, {
                    method: 'get',
                    content: 'application/json'
                });
                if (!response.ok) {
                    throw new Error("Errore HTML:" + response.status);
                };
                const data = await response.json();
                this.clienteData = data;
            } catch (error) {
                console.log(error.message);
            } finally {
                this.loading = false
            }
        },

        async addRigaPreventivo(e) {
            e.preventDefault();
            const form = document.querySelector('#formNuovoPreventivo');
            const formData = new FormData(form);
            console.log(`Indice PRIMA: ` + this.indiceRigheLavoro)
            const riga = {
                idRiga: this.idRiga,
                qty: formData.get('qty'),
                descrizione: formData.get('descrizione'),
                prezzo: formData.get('prezzo')
            };
            this.righeLavoro.push(riga);
            this.idRiga++;
            this.indiceRigheLavoro++;
            console.log(`Indice DOPO:  ` + this.indiceRigheLavoro)
            console.log(this.righeLavoro);
            // const url = `/preventivi/addrow`
        }
    },
    mounted() {
        this.loadClienti();
    },
    delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");