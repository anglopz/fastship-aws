import { Api } from "./client";

// Get API URL from environment variable, fallback to localhost for development
// In production (AWS), this should be set to https://api.fastship-api.com
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = new Api({
    baseURL: API_URL,
    securityWorker: (token) => {
        if (token) {
            return {
                headers: {
                    Authorization: `Bearer ${token}`,
                }
            }
        }
        return {}
    }
})

export default api// Test comment - CI/CD workflow verification 2026-01-21
