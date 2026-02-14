const TabellaClienti = {
    props: ["clienti_data"],
    template: `
    <table class="table my-0 sortable table-hover rounded-3 p-2 no-last-border">
        <thead>
            <tr>
                <th class="fw-bold pointer col-cliente" scope="col">Nominativo</th>
                <th title="Quantità di lavori del cliente" width="50px" class="fw-bold text-center pointer" scope="col">Qty</th>
                <th class="fw-bold pointer" scope="col">Email</th>
                <th class="fw-bold pointer" scope="col">Telefono</th>
                <th class="fw-bold pointer text-center" scope="col">Note</th>
            </tr>
        </thead>
        <tbody>
            <template v-if="clienti_data.length > 0">
                <tr v-for="cliente in clienti_data">
                   </td>
                    <td class="">
                        <a class="fw-bold text-decoration-none" :href="'/clienti/' + cliente.id">
                            <i :style="{ color : cliente.colore }" class="bi bi-person-circle me-2"></i>[[
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
                <td colspan="5" class="text-center">Nessun cliente trovato.</td>
            </tr>
        </tbody>
    </table>
    `,
    delimiters: ["[[", "]]"],
};