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

if (document.getElementById("app")) {
  const erpDashboardApp = Vue.createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        cards: [
          {
            title: "Prossimi impegni",
            icon: "bi-calendar-event",
            text: "Nessun impegno pianificato in questa anteprima.",
          },
          {
            title: "Task aperte",
            icon: "bi-list-check",
            text: "Le task operative verranno collegate alle API esistenti.",
          },
          {
            title: "Preventivi recenti",
            icon: "bi-receipt",
            text: "I preventivi recenti saranno disponibili nella dashboard ERP.",
          },
        ],
      };
    },
    template: `
      <section class="container-fluid px-0">
        <div class="mb-4">
          <p class="text-primary text-uppercase small fw-bold mb-2">Dashboard ERP</p>
          <h1 class="h3 mb-2">Benvenuto</h1>
          <p class="text-secondary mb-0">
            Punto di ingresso Vue per la migrazione progressiva del gestionale.
          </p>
        </div>

        <div class="row g-4">
          <div class="col-12 col-xl-4" v-for="card in cards" :key="card.title">
            <article class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-start gap-3">
                  <div class="rounded-3 bg-primary text-white d-inline-flex align-items-center justify-content-center flex-shrink-0" style="width: 44px; height: 44px;">
                    <i class="bi" :class="card.icon"></i>
                  </div>
                  <div>
                    <h2 class="h5 mb-2">[[ card.title ]]</h2>
                    <p class="text-secondary mb-0">[[ card.text ]]</p>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>
    `,
  });

  erpDashboardApp.mount("#app");
}
