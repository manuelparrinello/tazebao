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
            righe: [],
            idRiga: 0,
            indiceRiga: 0,
            loading: true,
            subtotale: 0,
            totali: [],
            clienteSelezionato: ""
        };
    },
    methods: {
        async sendForm(e) {
            e.preventDefault();
            const url = `/preventivi/nuovo`;
            const form = document.querySelector("#formNuovoPreventivo");
            const formData = new FormData(form);
            const response = await fetch(url, {
                method: "POST",
                body: formData,
            });
            if (!response.ok) {
                throw new Error("Errore richiesta: HTTP " + response.status);
            }
            const data = await response.json();
            let target_url = data["target_url"];
            window.open(target_url, `_blank`);
        },

        async loadClienti() {
            const url = `/api/clienti/getall`;
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
            this.clienti = data;
            for (const cliente of this.clienti) {}
        },

        async loadClienteDataByID(e) {
            e.preventDefault();
            const id = e.target.value;
            const url = `/api/clienti/get/${id}`;

            try {
                const response = await fetch(url, {
                    method: "get",
                    headers: {
                        "Accept": "application/json",
                    }
                });
                if (!response.ok) {
                    throw new Error("Errore HTML:" + response.status);
                }
                const data = await response.json();
                this.clienteData = data;
            } catch (error) {
                console.log(error.message);
            } finally {
                this.loading = false;
            }
        },

        calcSubtotale() {
            var riga = this.righe[this.indiceRiga];
            for (riga of this.righe) {
                this.totali.push(riga.totaleRiga);
            }
            this.subtotale += riga.totaleRiga;
        },

        async addRigaPreventivo(e) {
            e.preventDefault();
            console.clear();
            const form = document.querySelector("#formNuovoPreventivo");
            const formData = new FormData(form);
            const riga = {
                idRiga: this.idRiga,
                qty: formData.get("qty"),
                descrizione: formData.get("descrizione"),
                prezzo: formData.get("prezzo"),
                totaleRiga: Number(formData.get("qty")) * Number(formData.get("prezzo")),
            };
            this.righe.push(riga);
            this.calcSubtotale();
            this.idRiga++;
            this.indiceRiga++;
        },
    },
    mounted() {
        this.loadClienti();
    },
    delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");