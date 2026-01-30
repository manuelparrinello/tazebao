const TabellaLavori = {
    props: {
        lavori_data: Array,
        stato_lavori: Array,
        update_status: Function,
        filtro_stati: Function,
    },
    template: `
    <table class="table sortable mt-2 table-hover rounded-3" id="tabellaLavori">
            <thead>
                <tr>
                    <th class="fw-bold pointer text-center col-prio" scope="col">Prio</th>
                    <th class="fw-bold pointer col-desc" scope="col">Descrizione</th>
                    <th class="fw-bold pointer" scope="col">Prezzo</th>
                    <th class="fw-bold pointer text-center" scope="col">Stato</th>
                    <th class="fw-bold pointer text-center" scope="col">Inizio</th>
                    <th class="fw-bold pointer text-center" scope="col">Fine</th>
                    <th class="fw-bold pointer text-center" scope="col">Pagamento</th>
                    <th class="fw-bold pointer text-center col-note" scope="col">Note</th>
                    <th class="fw-bold pointer col-cliente" scope="col">Cliente</th>

                </tr>
            </thead>
            <tbody>
                <template v-if="lavori_data.length > 0">
                    <tr v-for="lavoro in lavori_data">
                    <td :sorttable_customkey="prioIndex(lavoro.priorita)" class="text-center col-prio">
                            <span v-html="prioPill(lavoro.priorita)" :class="prioClass(lavoro.priorita)">
                             </span>
                        </td>
                    <td><span class=""><a class="fw-bold text-decoration-underline" :href="'/lavori/' + lavoro.id ">[[ lavoro.descrizione ]]</a></span></td>
                        <td><i :style="{ color : lavoro.cliente.colore }" class="bi bi-person-circle me-2"></i><a
                                :href="/clienti/+ lavoro.cliente.id" class="text-decoration-none a-no-color">[[
                                lavoro.cliente.name ]]</a></td>
                        <td :sorttable_customkey="[[ lavoro.preventivato ]]" class="">[[ lavoro.preventivato
                            ]]€</td>
                        
                        <td class="text-center">
                        <select :class="statusColor(lavoro.stato)" @change="update_status($event, lavoro.id)" :id="'status_select_' + lavoro.id" name="status_select" class="form-control form-select form-select-sm status-select">
                            <option :value="lavoro.stato" selected>[[ lavoro.stato ]]</option>
                            <option v-for="stato in filtro_stati(lavoro.stato)" :value="[[ stato ]]">[[stato]]</option>
                        </select>
                        </td>
                        <td class="text-center">[[ lavoro.data_inizio ? new Date(lavoro.data_inizio).toLocaleDateString('it-IT') : '-' ]]</td>
                        <td class="text-center">[[ lavoro.data_fine || '-' ]]</td>
                        <td class="text-center">[[ lavoro.data_pagamento || '-' ]]</td>
                        <td class="text-center" id="note_td" v-html="renderNoteIcon(lavoro.note)"></td>
                    </tr>
                </template>
                <tr v-else>
                    <td colspan="10" class="text-center">Nessun lavoro trovato.</td>
                </tr>
            </tbody>
        </table>
    `,
    methods: {
        prioPill(prio) {
            if (prio === "Bassa") return `<i class="bi bi-emoji-smile"></i>`;
            if (prio === "Media") return `<i class="bi bi-emoji-neutral"></i>`;
            if (prio === "Alta") return `<i class="bi bi-emoji-angry"></i>`;
            return "";
        }, 

        statusColor(stato) {
            if (stato === "Da iniziare") {
                console.log("1. Caricamento colore in corso!");
                return "selectDaIniziare";
            } else if (stato === "In corso") {
                console.log("1. Caricamento colore in corso!");
                return "selectInCorso";
            } else if (stato === "In attesa") {
                console.log("1. Caricamento colore in corso!");
                return "selectInAttesa";
            } else {
                console.log("1. Caricamento colore in corso!");
                return "selectCompletato";
            }
        },

        prioIndex(prio) {
            if (prio === "Bassa") return 1;
            if (prio === "Media") return 2;
            if (prio === "Alta") return 3;
            return "";
        },

        prioClass(prio) {
            if (prio === "Bassa") return "prio-low";
            if (prio === "Media") return "prio-med";
            if (prio === "Alta") return "prio-high";
            return "";
        },

        renderNoteIcon(note) {
            if (note) {
                return `<i data-bs-placement="left" data-bs-toggle="tooltip" data-bs-title="${note}" class="bi bi-stickies" style="font-size: 1rem; color: #7e508d !important;"></i>`;
            }
            return "-";
        },
    },
    mounted() {

    },
    delimiters: ["[[", "]]"],
};