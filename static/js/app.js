/*-------------------*/
/* NUOVO CLIENTE APP */
/*-------------------*/
const nuovoClienteApp = Vue.createApp({
  data() {
    return {
      nomeCliente: "",
      telefono: "",
      email: "",
      colore: "",
      note: "",
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
    submitForm(e) {
      e.preventDefault();
      // Creazione di un oggetto FormData per inviare i dati del modulo
      const form = document.querySelector("#nuovoCliente");
      const formData = new FormData(form);
      formData.append("nomeCliente", this.nomeCliente);
      formData.append("telefono", this.telefono);
      formData.append("email", this.email);
      formData.append("colore", this.colore);
      formData.append("note", this.note);

      // Invio della richiesta POST al server
      fetch("/clienti/new", {
        method: "POST",
        body: formData,
      }).then((response) => {
        if (response.ok) {
          // Reindirizzamento alla pagina dei clienti dopo il successo
          window.alert("Cliente creato con successo!");
          window.location.href = "/clienti";
        } else {
          console.error("Errore durante la creazione del cliente.");
        }
      });
    },
  },
  delimiters: ["[[", "]]"],
}).mount("#formCliente");

/*--------------------*/
/*  NUOVO LAVORO APP  */
/*--------------------*/
const nuovoLavoroApp = Vue.createApp({
  data() {
    return {
      descrizione: "",
      dataInizio: "",
      dataFine: "",
      dataPagamento: "",
      stato: "",
      priorita: "",
      preventivato: "",
      cliente: "",
    };
  },
  methods: {
    submitForm(e) {
      e.preventDefault();
      const form = document.querySelector("#nuovoLavoro");
      const formData = new FormData(form);
      formData.append("descrizione", this.descrizione);
      formData.append("dataInizio", this.dataInizio);
      formData.append("dataFine", this.dataFine);
      formData.append("dataPagamento", this.dataPagamento);
      formData.append("stato", this.stato);
      formData.append("priorita", this.priorita);
      formData.append("preventivato", this.preventivato);
      formData.append("cliente", this.cliente);
      fetch("/lavori/new", {
        method: "POST",
        body: formData,
      }).then((response) => {
        if (response.ok) {
          window.alert("Lavoro creato con successo!");
          window.location.href = "/lavori";
        } else {
          console.error("Errore durante la creazione del lavoro.");
        }
      });
    },
  },
}).mount("#formLavoro");

/*--------------------*/
/*  CANCELLA CLIENTE  */
/*--------------------*/
function deleteCliente(id) {
  return fetch(`/clienti/${id}`, {
    method: "delete",
    headers: {
      Accept: "application/json",
    },
  });
}

async function clickForDeleteCliente(event, idCliente) {
  event.preventDefault();
  const utenteConferma = confirm("Sei sicuro di voler cancellare il cliente?");

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
}

/*-------------------*/
/*  CANCELLA LAVORO  */
/*-------------------*/

function deleteLavoro(id) {
  return fetch(`/lavori/${id}`, {
    method: "delete",
    headers: {
      Accept: "application/json",
    },
  });
}

async function clickForDeleteLavoro(event, idLavoro) {
  event.preventDefault();
  const conferma = confirm("Vuoi cancellare questo lavoro?");
  if (!conferma) return;

  try {
    const response = await deleteLavoro(idLavoro);
    if (!response) {
      const corpoRispostaTesto = await response.text();
      console.error("Errore response:", corpoRispostaTesto);
      throw new Error(
        `Errore durante l'eliminazione (HTTP ${response.status})`
      );
    }
    window.alert("Lavoro eliminato con successo!");
    window.location.href = "/lavori";
  } catch (errore) {
    alert(errore.message);
    console.error(errore);
  }
}

/*-------------------*/
/*  TUTTI I CLIENTI  */
/*-------------------*/

const getAllClienti = Vue.createApp({
  data() {
    return {
      clienti: [],
      loading: true,
      error: null,
      deletingID: null,
    }
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

    /* editClienti() --> DA FARE QUI SOTTO*/
  },
  mounted() {
    this.loadClienti();
    console.log(this.loadClienti())
  },
  delimiters: ["[[", "]]"],
}).mount('#clientiPage');



/*-------------------*/
/*   TUTTI I LAVORI  */
/*-------------------*/

const getAllLavori = Vue.createApp({
  data() {
    return {
      lavori: [],
      loading: true,
      error: null,
      deletingID: null,
    }
  },
  methods: {
    async loadLavori() {
      const url = `/api/lavori/getall`
      try {
        const response = await fetch(url, {
          method: 'get',
          headers: {
            'Accept': 'application/json'
          }
        })
        if (!response) {
          throw new error
        }
        this.lavori = await response.json();
      } catch (errore) {
        this.error = errore.message || "Errore imprevisto";
      } finally {
        /* setTimeout(() => {
          this.loading = false;
        }, 200000); */
        this.loading = false;
      }
    },

    prioClass(prio) {
      if (prio === "Bassa") return "prio-low";
      if (prio === "Media") return "prio-med";
      if (prio === "Alta") return "prio-high";
      return "";
    }
  },
  mounted() {
    this.loadLavori();
  },
  delimiters: ["[[", "]]"],
}
).mount('#lavoriPage')


/*-------------------*/
/*   CLIENTE PER ID  */
/*-------------------*/
const getSingleCliente = Vue.createApp({
  data() {
    return {
      lavori : [],
      
    }
  }
})