import { useEffect, useState, useRef } from "react";
import axios from "axios";
import "./tradeRequestFrame.css";

const TradingForm = ({ selectedStock, setSelectedStock }) => {
    const [stocks, setStocks] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [filteredStocks, setFilteredStocks] = useState([]);
    const userId = sessionStorage.getItem("user_id");

    const [orderType, setOrderType] = useState("BUY");
    const [price, setPrice] = useState("");
    const [volume, setVolume] = useState("");

    const [showDropdown, setShowDropdown] = useState(false);
    const wrapperRef = useRef();

    // Click outside -> close dropdown
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
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

    // Submit đặt lệnh
    const handlePlaceOrder = async (e) => {
        e.preventDefault();

        if (!selectedStock || !price || !volume) {
            alert("Vui lòng nhập đủ thông tin!");
            return;
        }

        try {
            const payload = {
                user_id: userId,
                stock_symbol: selectedStock,
                order_type: orderType,
                price: Number(price),
                quantity: Number(volume)
            };

            const res = await axios.post(
                'http://localhost:8000/trading/place',
                payload
            );

            console.log("Order created:", res.data);
            alert("Đặt lệnh thành công!");
        } catch (err) {
            console.error("Lỗi đặt lệnh:", err);
            alert("Đặt lệnh thất bại!");
        }
    };

    return (
        <form className="trade-frame" onSubmit={handlePlaceOrder}>
            <h2 className="trade-title">Đặt Lệnh</h2>
            {/* Phần tìm kiếm cổ phiếu */}
            <div className="stock-search-wrapper" ref={wrapperRef}>
                <label>Mã cổ phiếu</label>
                <input
                    type="text"
                    placeholder="Nhập mã cổ phiếu..."
                    value={selectedStock || searchQuery}
                    onChange={(e) => {
                        setSelectedStock(null);
                        setSearchQuery(e.target.value);
                        setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                />

                {showDropdown && (
                    <ul className="stock-list-overlay">
                        {filteredStocks.length > 0 ? (
                            filteredStocks.map(stock => (
                                <li
                                    key={stock.stock_symbol}
                                    onClick={() => {
                                        setSelectedStock(stock.stock_symbol);
                                        setSearchQuery("");
                                        setShowDropdown(false);
                                    }}
                                >
                                    {stock.stock_symbol} — {stock.stock_name}
                                </li>
                            ))
                        ) : (
                            <li className="no-result">Không tìm thấy</li>
                        )}
                    </ul>
                )}
            </div>

            {/* Phần đặt lệnh */}
            <div className="order-type-container">
                <label>Loại lệnh</label>
                <div className="order-toggle">
                    <button
                        type="button"
                        className={orderType === "BUY" ? "active-buy" : ""}
                        onClick={() => setOrderType("BUY")}
                    >
                        MUA
                    </button>

                    <button
                        type="button"
                        className={orderType === "SELL" ? "active-sell" : ""}
                        onClick={() => setOrderType("SELL")}
                    >
                        BÁN
                    </button>
                </div>
            </div>

            {/* GIÁ CẢ */}
            <div className="form-group">
                <label>Giá (VNĐ)</label>
                <input
                    type="number"
                    min="0"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="Nhập giá..."
                />
            </div>

            {/* VOLUME */}
            <div className="form-group">
                <label>Khối lượng</label>
                <input
                    type="number"
                    min="1"
                    value={volume}
                    onChange={(e) => setVolume(e.target.value)}
                    placeholder="Nhập khối lượng..."
                />
            </div>

            {/* SUBMIT BUTTON */}
            <button className="submit-order-btn" type="submit">
                Đặt lệnh {orderType === "BUY" ? "MUA" : "BÁN"}
            </button>
        </form>
    );
};

export default TradingForm;