import { useState, useEffect } from "react";
import { clearGeometries } from "../utils/map";

export default function useChat(apiKey, mapInstanceRef, onGeoData) {
  const [messages, setMessages] = useState([
    {
      // Define starting message of the chatbot
      text: "Hello there! Ask me some questions about the geometry of NRW. If you are not familiar with the federal system of NRW, we recommend to read the short introduction on our homepage",
      side: "left",
      time: new Date().toLocaleTimeString(),
      appeared: true,
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Remove old geometries from the map
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

    // Loading animation starts
    setIsLoading(true);

    var data = null;

    try {
      // Triggers the question-answering process in the backend and waits for the response
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          openAiKey: apiKey,
        }),
      });

      if (!res.ok) throw new Error("Server error");

      data = await res.json();
      data = data.result;

      setMessages((prev) => [
        ...prev,
        {
          text: data.result,
          side: "left",
          time: new Date().toLocaleTimeString(),
          appeared: true,
        },
      ]);

      // Intermediate_steps is undefined, when an error occured.
      if (data.intermediate_steps && onGeoData) {
        onGeoData(data.intermediate_steps);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          text: "⚠️ Backend not reachable",
          side: "left",
          time: new Date().toLocaleTimeString(),
          appeared: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  // Send message when Enter is pressed
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
