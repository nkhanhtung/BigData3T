import './UserForm.css';
import axios from 'axios';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const UserForm = ({ type, isActive }) => {
  const isSignUp = type === 'sign-up';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isSignUp) {
        // GỌI API ĐĂNG KÝ CHO USER
        const res = await axios.post('http://localhost:8000/user/register', {
          user_name: username,
          user_email: email,
          password_hash: password
        });
        alert('Đăng ký tài khoản thành công! Hãy đăng nhập ngay với tài khoản của bạn.');
        console.log(res.data);
      } else {
        // GỌI API ĐĂNG NHẬP CHO USER
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const res = await axios.post('http://localhost:8000/user/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        // LƯU LẠI TOKEN
        sessionStorage.setItem('user_token', res.data.current_token);
        alert('Đăng nhập thành công!');
        navigate('/homepage', { replace: true });
        console.log(res.data);
      }
    } catch (err) {
      console.error("API error:", err);
      console.log("Response data:", err.response?.data);
      alert(err.response?.data?.detail || err.message || 'Có lỗi xảy ra !');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`form-container ${type} ${isActive && isSignUp ? 'active' : ''}`}>
      <form onSubmit={handleSubmit}>
        <h1>{isSignUp ? 'Create Account' : 'Sign In'}</h1>
        <span>
          {isSignUp
            ? 'Start a new account to explore your potential now!'
            : 'Start your interesting experience with your own account!'}
        </span>
        {isSignUp && <input type='text'
                            placeholder='Username' 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)}
                            required/>}
        <input type='email'
               placeholder='Email'
               value={email}
               onChange={(e) => setEmail(e.target.value)}
               required/>
        <input type='password'
               placeholder='Password'
               value={password}
               onChange={(e) => setPassword(e.target.value)}
               required/>
        <button type='submit'>{isSignUp ? 'Sign Up' : 'Sign In'}</button>
        {loading && <div className="spinner"></div>}
      </form>
    </div>
  );
};

export default UserForm;