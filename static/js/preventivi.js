function formatPreventivoDate(value) {
  const formatter = window.erpDateFormatter?.formatDate;
  if (formatter) return formatter(value);
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  const parts = new Intl.DateTimeFormat("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).formatToParts(parsed);
  return parts
    .map((part) => (part.type === "month" ? part.value.charAt(0).toUpperCase() + part.value.slice(1) : part.value))
    .join("");
}

const preventivi = Vue.createApp({
  data() {
    return {
      preventivi: [],
    };
  },
  methods: {
    async fetchAllPreventivi() {
      const url = `/api/preventivi/getall`;
      try {
        const response = await fetch(url, {
          method: "get",
          headers: {
            Accept: "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Errore HTTP:" + response.status);
        }
        const data = await response.json();
        // console.log(data);
        this.preventivi = data;
        console.log(this.preventivi);
      } catch (err) {
        console.log(err);
      }
    },
    openPreventivo(id) {
      if (!id) return;
      window.location.href = `/preventivi/visualizza/${id}`;
    },
    formatDate(value) {
      return formatPreventivoDate(value);
    },
  },
  delimiters: ["[[", "]]"],
  mounted() {
    this.fetchAllPreventivi();
  },
}).mount("#preventivi");
