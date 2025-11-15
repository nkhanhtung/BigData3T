import './UserForm.css'
import './OverlayPanel.css'
import './UserLogin.css'
import axios from 'axios';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AdminLogin() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleAdminLogin = async (e) => {
        e.preventDefault();
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);
            // GỌI API ĐĂNG NHẬP CỦA ADMIN
            const res = await axios.post('http://localhost:8000/admin/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });
            // LƯU LẠI TOKEN
            sessionStorage.setItem('admin_token', res.data.access_token);
            alert('Đăng nhập vai trò admin thành công!');
            navigate('/homepage');
            console.log(res.data);
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.detail || 'Có lỗi xảy ra !');
        }
    };

    return (
        <div className='container'>
            {/* FORM ĐĂNG NHẬP */}
            <div className='form-container'>
                <form onSubmit={handleAdminLogin}>
                    <h1>Login for admin</h1>
                    <span>Login now!</span>
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
                    <button type='submit'>Sign In</button>
                </form>
            </div>
            {/* OVERLAY */}
            <div className='toggle-container'>
                <div className='toggle'>
                    <div className='toggle-panel toggle-right'>
                        <h1>Welcome back to CoCoFin</h1>
                        <p>Sign in with your account, admins!</p>
                    </div>
                </div>
            </div>
        </div>
    );
}