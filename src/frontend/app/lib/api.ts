import { Api } from "./client";

// Get API URL from environment variable, fallback to localhost for development
// In production (AWS), this should be set to https://api.fastship-api.com/api/v1
// Note: The /api/v1 prefix is required because backend routes are mounted at /api/v1
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

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
