import './index.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UserLogin from './components/Authentication/UserLogin';
import AdminLogin from './components/Authentication/AdminLogin';
import HomePage from './components/Homepage/homepage';
import PrivateRoute from './components/Authentication/PrivateRoute';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<UserLogin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/homepage"
          element={
            <PrivateRoute>
              <HomePage />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  </React.StrictMode>
);