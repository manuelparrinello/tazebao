const getLavoroByID = Vue.createApp({
    data() {
        return {
            lavoro: {},
            loading: true,
            error: "",
        };
    },
    methods: {
        async loadLavoroData() {
            const root = document.querySelector("#lavoroPage");
            const id = root.dataset.lavoroId;
            const url = `/api/lavori/get/${id}`;
            try {
                const response = await fetch(url, {
                    method: "get",
                    headers: {
                        Accept: "application/json",
                    },
                });
                if (!response.ok) {
                    throw new Error(
                        "Errore nella richiesta! HTTP" + response.status,
                    );
                }
                console.log("Dati JSON ricevuti!");
                const data = await response.json();
                this.lavoro = data;
            } catch (error) {
                this.error = error.message || "Errore imprevisto";
            } finally {
                this.loading = false;
            }
        },
    },
    mounted() {
        this.loadLavoroData();
    },
    delimiters: ["[[", "]]"],
}).mount("#lavoroPage");
