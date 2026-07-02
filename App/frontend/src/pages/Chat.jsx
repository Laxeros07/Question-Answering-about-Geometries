import PageTitle from "../components/PageTitle";
import { useRef, useState } from "react";
import Map from "../components/Map";
import { loadGeometries, exportLayerToGeoJSON } from "../utils/map";
import useChat from "../hooks/useChat";
import useApiKey from "../hooks/useApiKey";

// Generalization
import { processGeometry } from "../utils/geojson";
import { algorithms } from "../algorithms";

//const SAIA_BASE_URL = "https://chat-ai.academiccloud.de/v1";

// Fallback models in case the API is unavailable
const SAIA_MODELS = [
  { id: "gemma-4-31b-it", name: "gemma-4-31b-it" },
  //{ id: "qwen3.5-397b-a17b", name: "qwen3.5-397b-a17b" },
  { id: "qwen3-30b-a3b-instruct-2507", name: "qwen3-30b-a3b-instruct-2507" },
  { id: "glm-4.7", name: "glm-4.7" },
  { id: "meta-llama-3.1-8b-instruct", name: "meta-llama-3.1-8b-instruct" },
  //{ id: "mistral-large-3-675b-instruct-2512", name: "mistral-large-3-675b-instruct-2512" },
  { id: "qwen3.6-35b-a3b", name: "qwen3.6-35b-a3b" },
  { id: "teuken-7b-instruct-research", name: "teuken-7b-instruct-research" },
];

const OPENAI_MODELS = [
  { id: "gpt-5.4-mini", name: "gpt-5.4-mini" },
  { id: "gpt-5.4-nano", name: "gpt-5.4-nano" },
  { id: "gpt-4o", name: "gpt-4o" },
  { id: "gpt-4-turbo", name: "gpt-4-turbo" },
  { id: "gpt-3.5-turbo", name: "gpt-3.5-turbo" },
];

// List of all valid IDs
const ALL_MODEL_IDS = [
  ...OPENAI_MODELS.map((m) => m.id),
  ...SAIA_MODELS.map((m) => m.id),
];

const DEFAULT_MODEL = "gpt-5-nano";

export default function Chat() {
  const mapInstanceRef = useRef(null);
  const { apiKey, showModal, setShowModal, setApiKey, saveKey } = useApiKey();

  // Secure initialization with validation
  const [selectedModel, setSelectedModel] = useState(() => {
    const stored = localStorage.getItem("selectedModel");
    if (stored && ALL_MODEL_IDS.includes(stored)) {
      console.log("Loaded model from localStorage:", stored);
      return stored;
    }
    console.log("Using default model:", DEFAULT_MODEL);
    return DEFAULT_MODEL;
  });

  const isGwdgModel = !selectedModel.startsWith("gpt-");

  const [showProviderWarning, setShowProviderWarning] = useState(false);

  const handleModelChange = (e) => {
    const newModel = e.target.value;
    console.log("Model changed:", selectedModel, "->", newModel);
    const wasGwdg = !selectedModel.startsWith("gpt-");
    const isNowGwdg = !newModel.startsWith("gpt-");
    const providerChanged = wasGwdg !== isNowGwdg;

    setSelectedModel(newModel);
    localStorage.setItem("selectedModel", newModel);

    if (providerChanged) {
      setShowProviderWarning(true);
      // show warning for only 8 seconds
      // setTimeout(() => setShowProviderWarning(false), 8000);
    }
  };

  /** 
  // load SAIA-Models dynamically, when API-Key is there
  useEffect(() => {
    if (!apiKey) return;
    
    setLoadingModels(true);
    fetch(`${SAIA_BASE_URL}/models`, {
      headers: {
        "Accept": "application/json",
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      }
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        // SAIA sends { data: [{id: "model-name", ...}, ...] }
        if (data?.data && Array.isArray(data.data)) {
          const models = data.data.map((m) => ({
            id: m.id,
            name: m.id
              .split("-")
              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(" "),
          }));
          setSaiaModels(models);
        }
      })
      .catch((err) => {
        console.warn("Could not load SAIA models, using fallback:", err);
        // Fallback bleibt aktiv
      })
      .finally(() => setLoadingModels(false));
  }, [apiKey]);*/

  // Download
  const handleDownload = () => {
    if (!mapInstanceRef.current) {
      alert("Map is currently loading...");
      return;
    }
    selectedLayers.forEach((layerName) => {
      const layer =
        mapInstanceRef.current.layers[layerName];
      if (!layer) {
        console.error(
          "Layer not found:",
          layerName
        );
        return;
      }
      let geojson =
        layer.toGeoJSON();

      if (method !== "none") {
        const algorithm =
          algorithms[method];

        geojson = {
          ...geojson,

          features:
            geojson.features.map(
              (feature)=>({

                ...feature,

                geometry:
                  processGeometry(
                    feature.geometry,
                    algorithm,
                    Number(parameter)
                  )
              })
            )
        };
      }
      exportLayerToGeoJSON(
        layer,
        mapInstanceRef.current,
        `${layerName}_${method}.geojson`,
        geojson
      );
    });
  };

  // Load Geometries
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

  // generalization
  const [method, setMethod] = useState("none");
  const [parameter, setParameter] = useState("");
  const [selectedLayers, setSelectedLayers] = useState([
    "cityLayer",
    "districtLayer",
    "adLayer",
    "fsLayer"
  ]);

  const defaultParameters = {
    douglas: 50,
    visvalingam: 1000,
    chaikin: 1
  };
    

  return (
    <>
      {showModal && (
        <>
          <div className="modal fade show d-block" tabIndex="-1">
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content">
                <div className="modal-header d-flex justify-content-between">
                  <h4 className="modal-title">
                    {isGwdgModel ? "GWDG SAIA" : "OpenAI"} API Key
                  </h4>
                  <button
                    className="btn-close"
                    onClick={() => setShowModal(false)}
                  />
                </div>
                <div className="modal-body">
                  <p>
                    Enter your {isGwdgModel ? "GWDG SAIA" : "OpenAI"} API key:
                  </p>
                  <input
                    className="form-control"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveKey();
                    }}
                  />
                  <p className="fst-italic fw-light mt-2">
                    Without key, AGQA won't work.
                  </p>
                  {isGwdgModel && (
                    <p className="small text-muted mt-2">
                      Get your free GWDG SAIA key at{" "}
                      <a
                        href="https://docs.hpc.gwdg.de/services/saia/index.html"
                        target="_blank"
                        rel="noreferrer"
                      >
                        GWDG SAIA documentation
                      </a>
                      .
                    </p>
                  )}
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
          <div className="modal-backdrop fade show"></div>
        </>
      )}

      <PageTitle title="Chat" />
      <div className="container">
        <div className="row gy-4 gx-lg-3 mt-3 align-items-stretch">
          {/* LEFT SIDE - Chat */}
          <div className="col-lg-7 col-xs-12 mb-3 d-flex">
            <div className="chat_window w-100">
              <div className="top_menu d-flex justify-content-between align-items-center">
                <div className="title">Chat</div>

                {/* LLM Selection Dropdown */}
                <div className="d-flex gap-2 align-items-center">
                  {/* Provider Badge */}
                  <span
                    className={`badge ${isGwdgModel ? "bg-success" : "bg-primary"}`}
                    title={isGwdgModel ? "Using GWDG SAIA" : "Using OpenAI"}
                  >
                    {isGwdgModel ? "SAIA" : "OpenAI"}
                  </span>

                  <select
                    className="form-select form-select-sm"
                    value={selectedModel}
                    onChange={handleModelChange}
                    style={{ width: "auto", maxWidth: "200px" }}
                  >
                    <optgroup label="OpenAI">
                      {OPENAI_MODELS.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.name}
                        </option>
                      ))}
                    </optgroup>

                    <optgroup label="GWDG SAIA">
                      {SAIA_MODELS.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.name}
                        </option>
                      ))}
                    </optgroup>
                  </select>

                  <button
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => setShowModal(true)}
                  >
                    Change API Key
                  </button>
                </div>
              </div>
              {showProviderWarning && (
                <div
                  className="alert alert-warning alert-dismissible fade show m-2 py-2"
                  role="alert"
                >
                  <strong>Provider changed!</strong> You're now using{" "}
                  {isGwdgModel ? "GWDG SAIA" : "OpenAI"}.{" "}
                  <button
                    className="btn btn-sm btn-warning ms-2"
                    onClick={() => {
                      setShowModal(true);
                      setShowProviderWarning(false);
                    }}
                  >
                    Update API Key
                  </button>
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setShowProviderWarning(false)}
                    style={{ padding: "1rem" }}
                  ></button>
                </div>
              )}

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
              <div className="bottom_wrapper">
                <input
                  id="msg_input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="In which District lies..."
                />
                <div className="app_button_1" onClick={sendMessage}>
                  Send
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT SIDE - Map */}
          <div className="col-lg-5 col-xs-12 mb-3 d-flex">
            <div className="chat_window w-100 h-100">
              <div className="top_menu d-flex justify-content-between align-items-center">
                <div className="title">Germany</div>

                <div className="d-flex gap-2">

                  <button
                    className="btn btn-sm btn-outline-primary"
                    data-bs-toggle="modal"
                    data-bs-target="#generalizationModal"
                  >
                    Download & Generalization
                  </button>
                </div>
              </div>

              <div className="panel-group h-100">
                <Map mapInstanceRef={mapInstanceRef} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        className="modal fade"
        id="generalizationModal"
        tabIndex="-1"
        aria-labelledby="generalizationModalLabel"
        aria-hidden="true"
      >
        <div className="modal-dialog">
          <div className="modal-content">

            <div className="modal-header">
              <h5 className="modal-title" id="generalizationModalLabel">
                Download & Generalization
              </h5>
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="modal"
              />
            </div>

            <div className="modal-body">

              <div className="mb-3">

                <h6>Layer</h6>

                {[
                  { value: "cityLayer", label: "Cities" },
                  { value: "districtLayer", label: "Districts" },
                  { value: "adLayer", label: "Admin Districts" },
                  { value: "fsLayer", label: "Federal States" }
                ].map((layer) => (
                  <div className="form-check" key={layer.value}>

                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={layer.value}
                      checked={selectedLayers.includes(layer.value)}
                      onChange={(e) => {

                        if (e.target.checked) {
                          setSelectedLayers([
                            ...selectedLayers,
                            layer.value
                          ]);
                        } else {
                          setSelectedLayers(
                            selectedLayers.filter(
                              (item) => item !== layer.value
                            )
                          );
                        }

                      }}
                    />

                    <label
                      className="form-check-label"
                      htmlFor={layer.value}
                    >
                      {layer.label}
                    </label>

                  </div>
                ))}

              </div>

              <h6>Generalization</h6>
                <select
                    className="form-select"
                    value={method}
                    onChange={(e)=>{
                      setMethod(e.target.value);
                      setParameter(defaultParameters[e.target.value] ?? "");
                    }}
                >
                    <option value="none">None</option>
                    <option value="douglas">Douglas-Peucker</option>
                    <option value="visvalingam">Visvalingam-Whyatt</option>
                    <option value="chaikin">Chaikin</option>
                </select>
              
              {method !== "none" && (
                <div className="mt-3">
                    <label className="form-label">
                        {method === "douglas" && "Tolerance"}
                        {method === "visvalingam" && "Area Threshold"}
                        {method === "chaikin" && "Iterations"}
                    </label>

                    <input
                      type="text"
                      className="form-control"
                      inputMode="numeric"
                      value={parameter}
                      onChange={(e) => {

                        const value = e.target.value;

                        if (method === "chaikin") {

                          if (/^\d*$/.test(value)) {
                            setParameter(value);
                          }

                        } else {

                          if (/^\d*\.?\d*$/.test(value)) {
                            setParameter(value);
                          }

                        }

                      }}
                    />
                </div>
              )}
      
              <div className="d-flex gap-2 mt-3"
                style={{ justifyContent: "flex-end" }}>
                <button
                  className="btn btn-secondary"
                  data-bs-dismiss="modal"
                >
                  Cancel
                </button>

                <button
                  className="btn btn-primary"
                  onClick={handleDownload}
                >
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
