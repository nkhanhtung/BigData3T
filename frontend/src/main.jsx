import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UserLogin from './components/Authentication/UserLogin';
import AdminLogin from './components/Authentication/AdminLogin';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<UserLogin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
      </Routes>
    </Router>
  </React.StrictMode>
);