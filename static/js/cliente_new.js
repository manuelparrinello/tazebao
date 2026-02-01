const nuovoClienteApp = Vue.createApp({
    data() {
        return {
            nomeCliente: "",
            telefono: "",
            email: "",
            indirizzo: "",
            colore: "",
            note: "",
            citta: "",
            provincia: "",
            cap: "",
            p_iva: "",
            sdi: "",
            pec: "",
        };
    },
    computed: {
        inizialiNome() {
            if (this.nomeCliente.length) {
                return this.nomeCliente.charAt(0).toUpperCase();
            } else {
                return "-";
            }
        },
    },
    methods: {
        async submitFormNewCliente(e) {
            e.preventDefault();
            // Creazione di un oggetto FormData per inviare i dati del modulo
            const form = document.querySelector("#nuovoCliente");
            const formData = new FormData(form);
            formData.append('nome_cliente', this.nomeCliente);
            formData.append('indirizzo', this.indirizzo);
            formData.append('citta', this.citta);
            formData.append('cap', this.cap);
            formData.append('provincia', this.provincia);
            formData.append('email', this.email);
            formData.append('telefono', this.telefono);
            formData.append('p_iva', this.p_iva);
            formData.append('sdi', this.sdi);
            formData.append('pec', this.pec);
            formData.append('note', this.note);
            formData.append('colore', this.colore)

            try {
                const response = await fetch(`/clienti/new`, {
                    method: 'post',
                    body: formData
                })
                if (!response.ok) {
                    throw new Error('Errore richiesta! HTTP' + response.status);
                }
            } catch (error) {
                console.error(error);
            } finally {
                window.alert('Cliente aggiunto!');
                window.location.href = '/clienti';
            }
        },
    },
    delimiters: ["[[", "]]"],
}).mount("#formCliente");