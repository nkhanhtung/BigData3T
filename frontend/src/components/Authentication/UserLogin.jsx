import React, { useState } from 'react';
import AuthenticationForm from './UserForm';
import OverlayPanel from './OverlayPanel';
import './UserLogin.css';

{/* LOGIN AND REGISTER */}
export default function App() {
  const [isActive, setIsActive] = useState(false);

  const handleSignUpClick = () => {
    setIsActive(true);
  };

  const handleSignInClick = () => {
    setIsActive(false);
  };

  return (
    <div className={`container ${isActive ? 'active' : ''}`}>
      <AuthenticationForm type="sign-up" isActive={isActive} />
      <AuthenticationForm type="sign-in" isActive={isActive} />
      <OverlayPanel
        isActive={isActive}
        onSignUpClick={handleSignUpClick}
        onSignInClick={handleSignInClick}
      />
    </div>
  );
}