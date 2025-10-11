import './AuthenticationForm.css';

const AuthenticationForm = ({ type, isActive }) => {
  const isSignUp = type === 'sign-up';
  
  return (
    <div className={`form-container ${type} ${isActive && isSignUp ? 'active' : ''}`}>
      <form>
        <h1>{isSignUp ? 'Create Account' : 'Sign In'}</h1>
        <span>
          {isSignUp
            ? 'Start a new account to explore your potential now!'
            : 'Start your interesting experience with your own account!'}
        </span>
        {isSignUp && <input type="text" placeholder="Username" />}
        <input type="email" placeholder="Email" />
        <input type="password" placeholder="Password" />
        <button type="submit">{isSignUp ? 'Sign Up' : 'Sign In'}</button>
      </form>
    </div>
  );
};

export default AuthenticationForm;