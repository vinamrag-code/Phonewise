import { Link, useLocation } from 'react-router-dom';

function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="container nav-content">
        <Link to="/" className="nav-brand gradient-text">
          PhoneWise
        </Link>
        <ul className="nav-links">
          <li>
            <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
              Home
            </Link>
          </li>
          <li>
            <Link to="/recommend" className={location.pathname === '/recommend' ? 'active' : ''}>
              Recommend
            </Link>
          </li>
          <li>
            <Link to="/compare" className={location.pathname === '/compare' ? 'active' : ''}>
              Compare
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
