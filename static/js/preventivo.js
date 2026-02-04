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
            righeLavoro: [],
            indiceRiga: 0,
            loading: true,
            idRiga: 0,
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
            const parziali = [];
            for (const element of this.righeLavoro) {
                parziali.push(element.totaleRiga);
                return parziali;
            }
        },

        async addRigaPreventivo(e) {
            e.preventDefault();
            const form = document.querySelector("#formNuovoPreventivo");
            const formData = new FormData(form);

            const riga = {
                idRiga: this.idRiga,
                qty: formData.get("qty"),
                descrizione: formData.get("descrizione"),
                prezzo: formData.get("prezzo"),
                totaleRiga: Number(formData.get("qty")) * Number(formData.get("prezzo")),
            };
            this.righeLavoro.push(riga);
            this.idRiga++;
            this.indiceRiga++;
            console.log(`INDICE RIGA: ${this.indiceRiga}`);
            console.log(`ID RIGA: ${this.idRiga}`);
            console.log(`RIGA: ${this.righeLavoro[0]}`);
        },
    },
    mounted() {
        this.loadClienti();
    },
    delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");