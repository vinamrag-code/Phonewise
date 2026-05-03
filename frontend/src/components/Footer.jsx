function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <p>&copy; {new Date().getFullYear()} PhoneWise. All rights reserved.</p>
        <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Helping you make the smart choice.</p>
      </div>
    </footer>
  );
}

export default Footer;
