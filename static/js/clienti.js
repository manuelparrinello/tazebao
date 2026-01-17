const getAllClienti = Vue.createApp({
  components : {
    'tabella-clienti' : TabellaClienti
  },
  data() {
    return {
      clienti: [],
      loading: true,
      error: null,
      deletingID: null,
    };
  },
  methods: {
    async loadClienti() {
      const url = `/api/clienti/getall`;

      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error(`Errore richiesta! (HTTP ${response.status})`);
        }
        this.clienti = await response.json();
      } catch (errore) {
        this.error = errore.message || "Errore imprevisto";
      } finally {
        this.loading = false;
      }
    },

    deleteCliente(id) {
      return fetch(`/clienti/${id}`, {
        method: "delete",
        headers: {
          Accept: "application/json",
        },
      });
    },

    async clickForDeleteCliente(event, idCliente) {
      event.preventDefault();
      const utenteConferma = confirm(
        "Sei sicuro di voler cancellare il cliente?"
      );

      if (utenteConferma === false) {
        return;
      }

      try {
        const response = await deleteCliente(idCliente);
        console.log("DELETE status:", response.status);
        if (response.ok === false) {
          const corpoRispostaComeTesto = await response.text();
          console.error("Errore response:", corpoRispostaComeTesto);
          throw new Error(
            `Errore durante l'eliminazione (HTTP ${response.status})`
          );
        }
        alert("Cliente eliminato con successo!");
        window.location.href = "/clienti";
      } catch (errore) {
        alert(errore.message);
        console.error(errore);
      }
    },
  },

  mounted() {
    this.loadClienti();
    console.log(this.loadClienti());
  },
  delimiters: ["[[", "]]"],
}).mount("#clientiPage");

// DELETE CLIENTE //
function eliminaCliente(cliente_id) {
  if (!confirm("Sei sicuro di voler eliminare questo cliente?")) return;
  fetch(`/clienti/delete/${cliente_id}`)
    .then((response) => response.json())
    .then((msg) => {
      alert(msg);
      window.location.href = "/clienti";
    });
}
