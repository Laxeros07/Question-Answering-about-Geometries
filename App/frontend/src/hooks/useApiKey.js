import { useState, useEffect } from "react";

export default function useApiKey() {
  const [apiKey, setApiKey] = useState("");
  const [showModal, setShowModal] = useState(true);

  useEffect(() => {
    const savedKey = localStorage.getItem("openai_key");
    // If there already is a key in the local storage, hide the window.
    if (savedKey) {
      setApiKey(savedKey);
      setShowModal(false);
    }
  }, []);

  // validate if key is compatible with OpenAI or SAIA
  const validateKey = (key) => {
    if (!key || key.trim().length === 0) {
      return "Key cannot be empty";
    }

    // OpenAI Keys start with "sk-"
    if (key.startsWith("sk-")) {
      if (key.length < 20) {
        return "OpenAI key seems too short";
      }
      return null;
    }

    // GWDG SAIA Keys: alphanumerical Strings
    if (key.length >= 20) {
      return null;
    }

    return "Invalid key format. Expected OpenAI (sk-...) or GWDG SAIA key.";
  };

  // API key is stored in the local storage of the browser.
  const saveKey = () => {
    const error = validateKey(apiKey);
    if (error) {
      alert(error);
      return;
    }

    localStorage.setItem("apiKey", apiKey);
    setShowModal(false);
  };

  return {
    apiKey,
    setApiKey,
    showModal,
    setShowModal,
    saveKey,
  };
}
