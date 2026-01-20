const getAllLavori = Vue.createApp({
    components: {
        "tabella-lavori": TabellaLavori, // Registri il componente
    },
    data() {
        return {
            lavori: [],
            stato_lavori: ["Da iniziare", "In corso", "In attesa", "Completato"],
            loading: true,
            error: null,
            deletingID: null,
        };
    },
    methods: {

        populateExcludedStatuses(stato_attivo) {
            // 1. Prepariamo il secchio vuoto
            let listaFiltrata = [];
            // 2. Usiamo il ciclo che conosci: "Per ogni STATO dentro STATO_LAVORI"
            for (let stato of this.stato_lavori) {
                // 3. Se lo stato NON è quello selezionato (quello attivo)
                if (stato !== stato_attivo) {
                    // 4. Lo mettiamo nel secchio
                    listaFiltrata.push(stato);
                }
            }
            // 5. Restituiamo il risultato
            return listaFiltrata;
        },

        updateStatusStyle(e) {
            const selector = e.target;
            if (selector.value === "Da iniziare") {
                selector.classList.add('selectDaIniziare');
            } else if (selector.value === "In corso") {
                selector.classList.add('selectInCorso');
            } else if (selector.value === "In attesa") {
                selector.classList.add('selectInAttesa');
            } else {
                selector.classList.add('selectCompletato');
            }
        },

        async updateStatus(e, id) {
            const select = document.getElementById(`status_select_${id}`);
            const select_value = select.value;
            const url = `/lavori/${id}`;
            if (!this.stato_lavori.includes(select_value)) {
                return;
            }
            this.updateStatusStyle(e)
            try {
                const response = await fetch(url, {
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                    },
                    method: "patch",
                    body: JSON.stringify({
                        new_status: select_value,
                    }),
                });
                if (!response.ok) {
                    console.log("Errore nella richiesta! HTTP" + response.status);
                    throw new Error("Errore nella richiesta! HTTP" + response.status);
                }

                console.log("Dato aggiornato!");
                console.log(await response.json());
            } catch (error) {
                this.error = error.message || "Errore imprevisto";
            }
        },

        async loadLavori() {
            const url = `/api/lavori/getall`;
            try {
                const response = await fetch(url, {
                    method: "get",
                    headers: {
                        Accept: "application/json",
                    },
                });
                if (!response) {
                    throw new error();
                }
                this.lavori = await response.json();
            } catch (errore) {
                this.error = errore.message || "Errore imprevisto";
            } finally {
                this.loading = false;
                Vue.nextTick(() => {
                    var sorttable_table = document.getElementById("tabellaLavori");
                    if (sorttable_table && typeof sorttable !== "undefined") {
                        sorttable.makeSortable(sorttable_table);
                    }
                });
            }
        },

        styleStatus() {
            const select = document.getElementsByTagName(select);
            if (select.value === "Da iniziare") {
                select.classList.add('selectDaIniziare')
            }
        }
    },
    mounted() {
        this.loadLavori();
    },
    updated() {
        const tooltipTriggerList = document.querySelectorAll(
            '[data-bs-toggle="tooltip"]'
        );
        tooltipTriggerList.forEach((el) => {
            // Evita doppie inizializzazioni
            if (!bootstrap.Tooltip.getInstance(el)) {
                new bootstrap.Tooltip(el);
            }
        });
    },
    delimiters: ["[[", "]]"],
}).mount("#lavoriPage");