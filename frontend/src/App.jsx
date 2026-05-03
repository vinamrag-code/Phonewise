import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Compare from './pages/Compare';
import Recommend from './pages/Recommend';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/recommend" element={<Recommend />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
