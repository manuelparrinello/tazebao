const TabellaClienti = {
  props: ["clienti_data"],
  template: `
    <table class="table mt-2 sortable table-hover">
        <thead>
            <tr>
                <th width="80px" class="sorttable_nosort text-center" scope="col">Azioni</th>
                <th width="200px" class="pointer" scope="col">Nominativo</th>
                <th title="Quantità di lavori del cliente" width="50px" class="text-center pointer" scope="col">Qty</th>
                <th class="pointer" scope="col">Email</th>
                <th class="pointer" scope="col">Telefono</th>
                <th class="pointer text-center" scope="col">Note</th>
            </tr>
        </thead>
        <tbody>
            <template v-if="clienti_data.length > 0">
                <tr v-if="clienti_data" v-for="cliente in clienti_data">
                    <td class="fw-bold text-center">

                        <a :href="'/clienti/edit/' + cliente.id">
                            <button title="Modifica cliente" class="action-icon edit-icon me-1 text-warning">
                                <i class="bi bi-pencil"></i>
                            </button>
                        </a>

                        <a href="">
                            <button title="Cancella cliente" @click="clickForDeleteCliente( $event, cliente.id )"
                                class="action-icon delete-icon border-0">
                                <i class="bi bi-trash"></i>
                            </button>
                        </a>

                    </td>
                    <td class="">
                        <a class="fw-bold text-decoration-none" :href="'/clienti/' + cliente.id">
                            <span class="cliente-bullet" :style="{ backgroundColor: cliente.colore }"></span>[[
                            cliente.nome ]]
                        </a>
                    </td>
                    <td class="text-center">[[ cliente.count_lavori ]]</td>
                    <td>[[ cliente.email ]]</td>
                    <td>[[ cliente.telefono ]]</td>
                    <td class="text-center">[[ cliente.note ]]</td>
                </tr>
            </template>
            <tr v-else>
                <td colspan="6" class="text-center">Nessun cliente trovato.</td>
            </tr>
        </tbody>
    </table>
    `,
  delimiters: ["[[", "]]"],
};
