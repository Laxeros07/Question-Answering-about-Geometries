import PageTitle from "../components/PageTitle";
import { useRef } from "react";
import Map from "../components/Map";
import { loadGeometries, findKeysRecursively } from "../utils/map";
import useChat from "../hooks/useChat";
import useApiKey from "../hooks/useApiKey";

export default function Chat() {
  const mapInstanceRef = useRef(null);
  const { apiKey, showModal, setShowModal, setApiKey, saveKey } = useApiKey();

  // Callback function to handle the geodata received from the backend in useChat.js
  const handleGeoData = (steps) => {
    let ids = [];

    steps[1].context.forEach((item) => {
      findKeysRecursively(item, ids);
    });

    // Delete duplicates
    const uniqueIDs = ids.filter(
      (item, index, self) =>
        index ===
        self.findIndex((t) => t.id === item.id && t.name === item.name),
    );

    loadGeometries(uniqueIDs, mapInstanceRef.current);
  };

  const { messages, input, setInput, sendMessage, isLoading, handleKeyDown } =
    useChat(apiKey, mapInstanceRef, handleGeoData);

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
                <Map mapInstanceRef={mapInstanceRef} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
