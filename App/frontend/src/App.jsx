import Layout from "./components/Layout";
import Home from "./pages/Home";
import Info from "./pages/Info";
import Chat from "./pages/Chat";
import { Routes, Route } from "react-router-dom";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/info" element={<Info />} />
      </Routes>
    </Layout>
  );
}

export default App;
