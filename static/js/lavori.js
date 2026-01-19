const getAllLavori = Vue.createApp({
    components: {
        'tabella-lavori': TabellaLavori // Registri il componente
    },
    data() {
        return {
            lavori: [],
            stato_lavori: [
                'Completato',
                'In corso',
                'In attesa',
                'Da iniziare'
            ],
            loading: true,
            error: null,
            deletingID: null,
        };
    },
    methods: {
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

        async updateStatus(id) {
            const select = document.querySelector(`#status_select_${id}`);
            const select_value = select.value;
            if (!this.stato_lavori.includes(select_value)) {
                return
            }
            const url = `/lavori/${id}`;
            console.log(select_value);
            console.log(url);

            try {
                const response = await fetch(url, {
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    method: 'patch',
                    body: JSON.stringify({
                        'new_status': select_value
                    })
                });
                if (!response.ok) {
                    console.log('Errore nella richiesta! HTTP' + response.status)
                    throw new Error('Errore nella richiesta! HTTP' + response.status);
                }
                console.log('Dato aggiornato!');
                console.log(await response.json())
            } catch (error) {
                this.error = error.message || "Errore imprevisto";
            }
        }
    },
    mounted() {
        this.loadLavori();
    },
    updated() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        tooltipTriggerList.forEach(el => {
            // Evita doppie inizializzazioni
            if (!bootstrap.Tooltip.getInstance(el)) {
                new bootstrap.Tooltip(el)
            }
        })
    },
    delimiters: ["[[", "]]"],
}).mount("#lavoriPage");