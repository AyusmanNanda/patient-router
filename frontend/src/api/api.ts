import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_BACKEND,
    withCredentials: false,
    headers: {
        "Content-Type": "application/json",
    },
});

export default api;