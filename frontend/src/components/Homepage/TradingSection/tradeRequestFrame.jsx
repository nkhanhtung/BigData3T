import { useEffect, useState } from "react";

const TradingForm = () => {
    const [stocks, setStocks] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [filteredStocks, setFilteredStocks] = useState([]);
    const [selectedStock, setSelectedStock] = useState(null);

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

    return (
        <form className="trade-form">
            {/* Phần tìm kiếm cổ phiếu */}
            <input
                type="text"
                placeholder="Tìm kiếm cổ phiếu..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
            />
            <ul className="stock-list-overlay">
                {filteredStocks.map(stock => (
                    <li key={stock.stock_symbol} onClick={async () => {
                        setSearchQuery("");
                        setSelectedStock(stock.stock_symbol);
                    }}>
                        {stock.stock_symbol} - {stock.stock_name}
                    </li>
                ))}
            </ul>
            {/* Phần đặt lệnh mua/bán */}
        </form>
    );
};