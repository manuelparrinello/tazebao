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
            clienteSelezionato: "Seleziona cliente",
        };
    },
    methods: {
        dbg(e) {
            console.log("RAW:", JSON.stringify(e.target.value));
            console.log("MODEL:", JSON.stringify(this.descrizione));
        },
        autoResize(e) {
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
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
        },

        async loadClienteDataByID(e) {
            e.preventDefault();
            const id = e.target.value;
            const url = `/api/clienti/get/${id}`;

            try {
                const response = await fetch(url, {
                    method: "get",
                    headers: {
                        Accept: "application/json",
                    },
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
            this.totali = [];
            this.subtotale = 0;

            for (const riga of this.righe) {
                const totaleRiga = Number(riga.totaleRiga) || 0;
                this.totali.push(totaleRiga);
                this.subtotale += totaleRiga;
            }
        },

        async addRigaPreventivo(e) {
            e.preventDefault();
            if (this.clienteSelezionato === "Seleziona cliente") {
                window.alert("Seleziona cliente!");
                return;
            }
            console.clear();
            const form = document.querySelector("#formNuovoPreventivo");
            const formData = new FormData(form);
            const qty = Number(formData.get("qty")) || 0;
            const prezzo = Number(formData.get("prezzo")) || 0;
            const descrizione = String(
                formData.get("descrizione") || "",
            ).trim();
            const riga = {
                idRiga: this.idRiga,
                qty: qty,
                descrizione: descrizione,
                prezzo: prezzo,
                totaleRiga:
                    Number(formData.get("qty")) *
                    Number(formData.get("prezzo")),
            };
            this.righe.push(riga);
            this.calcSubtotale();
            console.log(this.subtotale);
            this.idRiga++;
            this.indiceRiga++;
        },

        viewPreventivo(id) {
            const url = `/preventivi/visualizza/${id}`;
            window.location.href = url;
        },

        async sendForm(e) {
            e.preventDefault();
            const url = `/preventivi/nuovo`;
            const dataToSend_raw = {
                cliente_id: this.clienteData.id,
                righe: this.righe,
            };
            const dataToSend = JSON.stringify(dataToSend_raw);
            const response = await fetch(url, {
                method: "POST",
                body: dataToSend,
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (!response.ok) {
                throw new Error("Errore richiesta: HTTP " + response.status);
            }
            const data = await response.json();
            var preventivo_id = data.preventivo_id;
            console.log(preventivo_id);
            var conferma = window.confirm(
                "Preventivo salvato. Vuoi visualizzarlo?",
            );
            if (!conferma) {
                window.location.href = "/clienti";
            }
            this.viewPreventivo(preventivo_id);
        },
    },
    mounted() {
        this.loadClienti();
    },
    delimiters: ["[[", "]]"],
}).mount("#nuovoPreventivo");
