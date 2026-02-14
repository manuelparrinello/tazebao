const preventivi = Vue.createApp({
    data() {
        return {
            preventivi: [],
        };
    },
    methods: {
        async fetchAllPreventivi() {
            const url = `/api/preventivi/getall`;
            const response = await fetch(url, {
                method: "get",
                headers: {
                    Accept: "application/json",
                },
            });
            const data = await response.json();
            console.log(data);
            this.preventivi = data;
        },
    },
    delimiters: ["[[", "]]"],
    mounted() {
        this.fetchAllPreventivi();
    },
}).mount("#preventivi");
