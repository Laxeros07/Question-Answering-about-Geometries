import PageTitle from "../components/PageTitle";
import Map from "../components/Map";
import { useRef, useState, useEffect } from "react";

export default function Chat() {
  const [apiKey, setApiKey] = useState("");
  const [showModal, setShowModal] = useState(true);

  useEffect(() => {
    const savedKey = localStorage.getItem("openai_key");

    if (savedKey) {
      setApiKey(savedKey);
      setShowModal(false);
    }
  }, []);

  const saveKey = () => {
    if (!apiKey.startsWith("sk-")) {
      alert("Invalid key format");
      return;
    }
    localStorage.setItem("openai_key", apiKey);
    setShowModal(false);
  };

  const [messages, setMessages] = useState([
    {
      text: "Hello there! Ask me some questions about the geometry of NRW. If you are not familiar with the federal system of NRW, we recommend to read the short introduction on our homepage",
      side: "left",
      time: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const question = input;
    setInput("");

    setMessages((prev) => [
      ...prev,
      {
        text: question,
        side: "right",
        time: new Date().toLocaleTimeString(),
        appeared: false,
      },
    ]);

    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          openAiKey: apiKey,
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          text: data.result,
          side: "left",
          time: new Date().toLocaleTimeString(),
          appeared: false,
        },
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  useEffect(() => {
    const el = document.querySelector(".messages");
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    setMessages((prev) =>
      prev.map((msg, i) =>
        i === prev.length - 1 ? { ...msg, appeared: true } : msg,
      ),
    );
  }, [messages.length]);

  return (
    <>
      {showModal && (
        <>
          <div className="modal fade show d-block" tabIndex="-1">
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header d-flex justify-content-between">
                  <h4 className="modal-title">OpenAI API Key</h4>
                  <button
                    className="btn-close"
                    onClick={() => setShowModal(false)}
                  />
                </div>

                <div className="modal-body">
                  <p>Enter your OpenAI API key:</p>

                  <input
                    className="form-control"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        saveKey();
                      }
                    }}
                  />

                  <p className="fst-italic fw-light mt-2">
                    Without key, Chat with NRW won't work.
                  </p>
                </div>

                <div className="modal-footer">
                  <button
                    className="btn saveBtn btn-danger ms-auto"
                    onClick={saveKey}
                  >
                    Save key
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* BACKDROP */}
          <div className="modal-backdrop fade show"></div>
        </>
      )}
      <PageTitle title="Chat" />
      <div className="container">
        <div className="row gy-4 gx-lg-3 mt-3">
          {/* RIGHT SIDE */}
          <div className="col-lg-7 col-xs-12 mb-3">
            <div className="chat_window">
              <div className="top_menu">
                <div className="title">ChatBot - Shadowfax</div>

                <button
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => setShowModal(true)}
                >
                  Change API Key
                </button>
              </div>

              {/* dynamically rendered */}
              <ul className="messages">
                {messages.map((msg, i) => (
                  <li
                    key={i}
                    className={`message ${msg.side} ${msg.appeared ? "appeared" : ""}`}
                  >
                    {msg.side === "left" && <div className="avatar"></div>}
                    <div className="text_wrapper">
                      <div className="text">{msg.text}</div>
                      <div className="timestamp">{msg.time}</div>
                    </div>
                    {msg.side === "right" && <div className="avatar"></div>}
                  </li>
                ))}

                {isLoading && (
                  <li className="message left appeared">
                    <div className="avatar"></div>
                    <div className="l-gif"></div>
                  </li>
                )}
              </ul>

              {/* input */}
              <div className="bottom_wrapper">
                <input
                  id="msg_input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Say Hi to begin chat..."
                />
                <div className="app_button_1" onClick={sendMessage}>
                  Send
                </div>
              </div>
            </div>
          </div>

          {/* LEFT SIDE */}
          <div className="col-lg-5 col-xs-12 mb-3">
            <div className="chat_window">
              <div className="top_menu">
                <div className="title">NRW</div>
              </div>

              <div className="panel-group">
                <Map />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
