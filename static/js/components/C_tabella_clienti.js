const TabellaClienti = {
    props: ["clienti_data"],
    template: `
    <table class="table mt-2 sortable table-hover border rounded-2 p-2">
        <thead>
            <tr>
                <th class="fw-bold col-actions sorttable_nosort text-center" scope="col">Azioni</th>
                <th width="200px" class="fw-bold pointer" scope="col">Nominativo</th>
                <th title="Quantità di lavori del cliente" width="50px" class="fw-bold text-center pointer" scope="col">Qty</th>
                <th class="fw-bold pointer" scope="col">Email</th>
                <th class="fw-bold pointer" scope="col">Telefono</th>
                <th class="fw-bold pointer text-center" scope="col">Note</th>
            </tr>
        </thead>
        <tbody>
            <template v-if="clienti_data.length > 0">
                <tr v-for="cliente in clienti_data">
                    <td class="fw-bold text-center">

                        <a title="Modifica cliente" class="action-icon edit-icon me-2 text-warning" :href="'/clienti/edit/' + cliente.id">
                                <i class="bi bi-pencil"></i>
                        </a>

                        <a title="Cancella cliente" @click.prevent="$emit('delete', cliente.id)" class="action-icon delete-icon" href="">
                                <i class="bi bi-trash"></i>
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
