import { Route, Routes, Navigate } from "react-router-dom";
import Landing from "./routes/Landing";
import Preferences from "./routes/Preferences";
import Results from "./routes/Results";
import Compare from "./routes/Compare";
import Admin from "./routes/Admin";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/preferences" element={<Preferences />} />
      <Route path="/results" element={<Results />} />
      <Route path="/compare" element={<Compare />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

