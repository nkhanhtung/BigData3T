import './navigation_bar.css';
import logo from '../../resources/logo.png';
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

import StockDashboardOverlay from '../StockDashboard/stockDashboardOverlay';

const NavBar = () => {
    const [showMenu, setShowMenu] = useState(false);
    const [showConfirmLogout, setShowConfirmLogout] = useState(false);

    const [showSearchOverlay, setShowSearchOverlay] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [stocks, setStocks] = useState([]);
    const [filteredStocks, setFilteredStocks] = useState([]);

    const [selectedStock, setSelectedStock] = useState(null); // mã stock đang chọn
    const [showStockDashboard, setShowStockDashboard] = useState(false); // hiển thị overlay thông tin stock

    const menuRef = useRef(null);
    const navigate = useNavigate();

    const toggleMenu = () => {
        setShowMenu(!showMenu);
    }

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Lấy danh sách cổ phiếu từ backend khi component mount
    useEffect(() => {
        const fetchStocks = async () => {
            try {
                const res = await axios.get("http://localhost:8000/visualization/stocks/list");
                setStocks(res.data.stocks);
                setFilteredStocks(res.data.stocks);
            } catch (err) {
                console.error("Lỗi lấy danh sách cổ phiếu:", err);
            }
        };
        fetchStocks();
    }, []);

    // Lọc danh sách khi người dùng gõ
    useEffect(() => {
        const filtered = stocks.filter(
            (s) =>
                s.stock_symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                s.stock_name.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setFilteredStocks(filtered);
    }, [searchQuery, stocks]);

    // Logic đăng xuất
    const confirmLogout = async () => {
        const token = sessionStorage.getItem('user_token');
        try {
            if (token) {
                await axios.post(
                    'http://localhost:8000/user/logout',
                    {},
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
            }
        } catch (err) {
            console.error('Logout error:', err.response?.data || err.message);
        } finally {
            sessionStorage.removeItem('user_token');
            navigate('/', { replace: true });
        }
    };

    return (
        <>
            <nav className="navbar">
                {/* Logo và tên web */}
                <div className="navbar-left">
                    <img src={logo} alt="CocoFin Logo" className="logo" />
                    <span className="web-name">CocoFin</span>
                </div>

                {/* Menu nút */}
                <div className="navbar-center">
                    <button className="nav-button" onClick={() => navigate('/homepage/market')}>Thị trường</button>
                    <button className="nav-button" onClick={() => navigate('/homepage/trading')}>Giao dịch</button>
                    <button className="nav-button">Danh mục</button>
                    <button className="nav-button" onClick={() => navigate('/homepage/chart')}>Biểu đồ</button>
                </div>

                {/* Thanh tìm kiếm & nút truy cập hồ sơ tài khoản */}
                <div className="navbar-right" ref={menuRef}>
                    <div className="search-fake" onClick={() => setShowSearchOverlay(true)}>
                        <i className="fas fa-search"></i>
                        <span className="search-placeholder">Tìm kiếm cổ phiếu...</span>
                    </div>

                    <i className="fas fa-user-circle user-icon" onClick={toggleMenu}></i>

                    {showMenu && (
                        <div className='user-menu'>
                            <div className='menu-item' onClick={() => alert('Chuyển tới trang tài khoản')}>
                                Tài khoản
                            </div>

                            <div className='menu-item logout' onClick={() => setShowConfirmLogout(true)}>
                                Đăng xuất
                            </div>
                        </div>
                    )}
                </div>
            </nav>

            {/* Overlay search */}
            {showSearchOverlay && (
                <div className='search-overlay' onClick={() => setShowSearchOverlay(false)}>
                    <div className='search-overlay-box' onClick={e => e.stopPropagation()}>
                        <input
                            type="text"
                            placeholder="Tìm kiếm cổ phiếu..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            autoFocus
                        />
                        <ul className='search-overlay-list'>
                            {filteredStocks.map(stock => (
                                <li key={stock.stock_symbol} onClick={async () => {
                                    setShowSearchOverlay(false);
                                    setSearchQuery("");
                                    setSelectedStock(stock.stock_symbol);
                                    setShowStockDashboard(true);
                                }}>
                                    {stock.stock_symbol} - {stock.stock_name}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Dashboard Overlay */}
            {showStockDashboard && (
                <StockDashboardOverlay
                    stockSymbol={selectedStock}
                    onClose={() => setShowStockDashboard(false)}
                />
            )}

            {/* Hộp thoại xác nhận đăng xuất */}
            {showConfirmLogout && (
                <div className="logout-overlay">
                    <div className="logout-box">
                        <h3>Bạn có chắc chắn muốn đăng xuất?</h3>
                        <div className="logout-buttons">
                            <button
                                className="btn-confirm"
                                onClick={() => {
                                    setShowConfirmLogout(false);
                                    confirmLogout();
                                }}
                            >
                                Có
                            </button>
                            <button
                                className="btn-cancel"
                                onClick={() => setShowConfirmLogout(false)}
                            >
                                Không
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default NavBar;