import './OverlayPanel.css';

const OverlayPanel = ({ isActive, onSignUpClick, onSignInClick }) => {
  return (
    <div className={`toggle-container ${isActive ? 'active' : ''}`}>
      <div className={`toggle ${isActive ? 'active' : ''}`}>
        <div className="toggle-panel toggle-left">
          <h1>Welcome back to CoCoFin</h1>
          <p>Enter your personal details to use all of site features</p>
          <button className="hidden" onClick={onSignInClick}>
            Sign In
          </button>
        </div>
        <div className="toggle-panel toggle-right">
          <h1>Welcome to CoCoFin</h1>
          <p>Register with your personal details to use all of site features</p>
          <button className="hidden" onClick={onSignUpClick}>
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
};

export default OverlayPanel;