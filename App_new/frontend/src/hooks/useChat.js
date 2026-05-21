import { useState, useEffect } from "react";
import { clearGeometries } from "../utils/map";
import { API_BASE_URL } from "../utils/constants";

export default function useChat(
  apiKey,
  mapInstanceRef,
  onGeoData,
  selectedModel,
) {
  const [messages, setMessages] = useState([
    {
      text: "Hello there! Ask me some questions about the geometry of Germany. If you are not familiar with the federal system of NRW, we recommend to read the short introduction on our homepage",
      side: "left",
      time: new Date().toLocaleTimeString(),
      appeared: true,
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    if (mapInstanceRef.current) {
      clearGeometries(mapInstanceRef);
    }

    const question = input;
    setInput("");

    setMessages((prev) => [
      ...prev,
      {
        text: question,
        side: "right",
        time: new Date().toLocaleTimeString(),
        appeared: true,
      },
    ]);

    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          openAiKey: apiKey,
          selectedModel: selectedModel,
        }),
      });

      if (!res.ok) {
        throw new Error(data.details || data.error || "Unknown server error");
      }

      const data = await res.json();
      //console.log("Backend Response:", data);

      const resultData = data.result.result;

      if (!resultData || !resultData.verbalized) {
        throw new Error(
          "Unexpected response structure: " + JSON.stringify(data),
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          text: resultData.verbalized,
          side: "left",
          time: new Date().toLocaleTimeString(),
          appeared: true,
        },
      ]);

      if (resultData.start && onGeoData && resultData.target) {
        onGeoData([resultData.start, ...resultData.target]);
      }
    } catch (err) {
      // Backend not reachable
      if (err instanceof TypeError) {
        err.message = "Backend not reachable";
      }
      setMessages((prev) => [
        ...prev,
        {
          text: "Error: " + err.message,
          side: "left",
          time: new Date().toLocaleTimeString(),
          appeared: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    const el = document.querySelector(".messages");
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return {
    messages,
    input,
    setInput,
    sendMessage,
    isLoading,
    handleKeyDown,
  };
}
