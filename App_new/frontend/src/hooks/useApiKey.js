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

  // API key is stored in the local storage of the browser.
  const saveKey = () => {
    if (!apiKey.startsWith("sk-")) {
      alert("Invalid key format");
      return;
    }
    localStorage.setItem("openai_key", apiKey);
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
