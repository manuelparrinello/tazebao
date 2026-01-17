const TabellaLavori = {
  props: ["lavori_data"], // Qui dichiari il nome del "tubo"
  template: `
    <table class="table sortable mt-2 table-hover" id="tabellaLavori">
            <thead>
                <tr>
                    <th class="pointer col-desc" scope="col">Descrizione</th>
                    <th class="pointer col-cliente" scope="col">Cliente</th>
                    <th class="pointer text-center" scope="col">Preventivato</th>
                    <th class="pointer text-center" scope="col">Prio</th>
                    <th class="pointer text-center" scope="col">Stato</th>
                    <th class="pointer text-center" scope="col">Data inizio</th>
                    <th class="pointer text-center" scope="col">Data fine</th>
                    <th class="pointer text-center" scope="col">Data pagamento</th>
                    <th class="pointer text-center col-note" scope="col">Note</th>

                </tr>
            </thead>
            <tbody>
                <template v-if="lavori_data.length > 0">
                    <tr v-for="lavoro in lavori_data">
                        <td><span class="">[[ lavoro.descrizione ]]</span></td>
                        <td><span class="cliente-bullet" :style="{ backgroundColor: lavoro.cliente.colore }"></span><a
                                :href="/clienti/+ lavoro.cliente.id" class="fw-bold text-decoration-none">[[
                                lavoro.cliente.name ]]</a></td>
                        <td :sorttable_customkey="[[ lavoro.preventivato ]]" class="text-center">[[ lavoro.preventivato
                            ]]€</td>
                        <td :sorttable_customkey="prioIndex(lavoro.priorita)" class="text-center">
                            <span class="prio-pill" :class="prioClass(lavoro.priorita)">
                                [[ lavoro.priorita ]]
                            </span>
                        </td>
                        <td class="text-center">[[ lavoro.stato ]]</td>
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
  delimiters: ["[[", "]]"],
};
