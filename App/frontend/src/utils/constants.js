const apiUrl = process.env.REACT_APP_API_URL || "";

if (!apiUrl) {
  throw new Error("REACT_APP_API_URL is not defined");
}

export const API_BASE_URL = apiUrl;
