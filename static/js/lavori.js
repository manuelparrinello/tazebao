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
            classesStatus: ["selectDaIniziare", "selectInCorso", "selectInAttesa", "selectCompletato"]
        };
    },
    methods: {
        populateExcludedStatuses(stato_attivo) {
            let listaFiltrata = [];
            for (let stato of this.stato_lavori) {
                if (stato !== stato_attivo) {
                    listaFiltrata.push(stato);
                }
            }
            // 5. Restituiamo il risultato
            return listaFiltrata;
        },

        updateStatusStyle(e) {
            const selector = e.target;
            // 1. Definiamo l'elenco di tutte le classi "stato" che gestiamo
            const classiStato = ["selectDaIniziare", "selectInCorso", "selectInAttesa", "selectCompletato"];

            // 2. Rimuoviamo tutte queste classi dal selector (pulizia totale)
            selector.classList.remove(...classiStato);

            // 3. Determiniamo la nuova classe in base al valore
            let newClass = "";

            if (selector.value === "Da iniziare") {
                newClass = "selectDaIniziare";
            } else if (selector.value === "In corso") {
                newClass = "selectInCorso";
            } else if (selector.value === "In attesa") {
                newClass = "selectInAttesa";
            } else {
                newClass = "selectCompletato";
            }

            // 4. Aggiungiamo solo la classe specifica
            selector.classList.add(newClass);

        },

        async updateStatus(e, id) {
            const select = document.getElementById(`status_select_${id}`);
            const select_value = select.value;
            const url = `/lavori/${id}`;
            if (!this.stato_lavori.includes(select_value)) {
                return;
            }

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
                console.log(await response.json());
            } catch (error) {
                this.error = error.message || "Errore imprevisto";
            }
            this.updateStatusStyle(e);
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