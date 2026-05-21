import PageTitle from "../components/PageTitle";
import { useRef, useState } from "react";
import Map from "../components/Map";
import { loadGeometries, findKeysRecursively, exportLayerToGeoJSON } from "../utils/map"; 
import useChat from "../hooks/useChat";
import useApiKey from "../hooks/useApiKey";

export default function Chat() {
  const mapInstanceRef = useRef(null);
  const { apiKey, showModal, setShowModal, setApiKey, saveKey } = useApiKey();
  
  // State for currently selected Model
  const [selectedModel, setSelectedModel] = useState("gpt-5-nano"); 

  const handleDownload = (layerKey) => {
    if (mapInstanceRef.current) {
      exportLayerToGeoJSON(layerKey, mapInstanceRef.current, `${layerKey}.geojson`);
    } else {
      alert("Map is currently loaded...");
    }
  };

  const handleGeoData = (ids) => {
    const uniqueIDs = ids.filter(
      (item, index, self) =>
        index ===
        self.findIndex((t) => t.id === item.id && t.name === item.name),
    );
    loadGeometries(uniqueIDs, mapInstanceRef.current);
  };

  // pass selectedModel to useChat
  const { messages, input, setInput, sendMessage, isLoading, handleKeyDown } =
    useChat(apiKey, mapInstanceRef, handleGeoData, selectedModel);

  return (
    <>
      {showModal && (
        <>
          <div className="modal fade show d-block" tabIndex="-1">
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header d-flex justify-content-between">
                  <h4 className="modal-title">OpenAI API Key</h4>
                  <button className="btn-close" onClick={() => setShowModal(false)} />
                </div>
                <div className="modal-body">
                  <p>Enter your OpenAI API key:</p>
                  <input
                    className="form-control"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") saveKey(); }}
                  />
                  <p className="fst-italic fw-light mt-2">Without key, Chat with Germany won't work.</p>
                </div>
                <div className="modal-footer">
                  <button className="btn saveBtn btn-danger ms-auto" onClick={saveKey}>Save key</button>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop fade show"></div>
        </>
      )}

      <PageTitle title="Chat" />
      <div className="container">
        <div className="row gy-4 gx-lg-3 mt-3">
          {/* RIGHT SIDE */}
          <div className="col-lg-7 col-xs-12 mb-3">
            <div className="chat_window">
              <div className="top_menu d-flex justify-content-between align-items-center">
                <div className="title">ChatBot - Shadowfax</div>
                
                {/* LLM Selection Dropdown */}
                <div className="d-flex gap-2">
                  <select 
                    className="form-select form-select-sm" 
                    value={selectedModel} 
                    onChange={(e) => setSelectedModel(e.target.value)}
                    style={{ width: 'auto' }}
                  >
                    <option value="gpt-5-nano">GPT-5 Nano</option>
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    {/* TODO: weitere Modelle aus der SAIA-Liste ergänzen */}
                  </select>

                  <button className="btn btn-sm btn-outline-secondary" onClick={() => setShowModal(true)}>
                    Change API Key
                  </button>
                </div>
              </div>
              
              <ul className="messages">
                {messages.map((msg, i) => (
                  <li key={i} className={`message ${msg.side} ${msg.appeared ? "appeared" : ""}`}>
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
              <div className="bottom_wrapper">
                <input
                  id="msg_input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Say Hi to begin chat..."
                />
                <div className="app_button_1" onClick={sendMessage}>Send</div>
              </div>
            </div>
          </div>

          {/* LEFT SIDE */}
          <div className="col-lg-5 col-xs-12 mb-3">
            <div className="chat_window">
              <div className="top_menu d-flex justify-content-between align-items-center">
                <div className="title">Germany</div>
                
                <div className="dropdown">
                  <button 
                    className="btn btn-sm btn-outline-primary dropdown-toggle" 
                    type="button" 
                    id="downloadDropdown" 
                    data-bs-toggle="dropdown" 
                    aria-expanded="false"
                  >
                    Download Data as GeoJSON
                  </button>
                  <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="downloadDropdown">
                    <li><button className="dropdown-item" onClick={() => handleDownload('cityLayer')}>Cities</button></li>
                    <li><button className="dropdown-item" onClick={() => handleDownload('districtLayer')}>Districts</button></li>
                    <li><button className="dropdown-item" onClick={() => handleDownload('adLayer')}>Admin Districts</button></li>
                    <li><button className="dropdown-item" onClick={() => handleDownload('fsLayer')}>Federal States</button></li>
                  </ul>
                </div>
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
