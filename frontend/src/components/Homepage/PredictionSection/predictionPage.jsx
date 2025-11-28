import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";
import "./predictionPage.css";

// Đăng ký Chart.js
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const PredPage = () => {
    const [searchQuery, setSearchQuery] = useState("");
    const [stocks, setStocks] = useState([]);
    const [filteredStocks, setFilteredStocks] = useState([]);
    const [selectedStock, setSelectedStock] = useState(null);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [predictionType, setPredictionType] = useState("realtime");
    const [predictions, setPredictions] = useState([]);
    const [historicalData, setHistoricalData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [stockInfo, setStockInfo] = useState(null);

    const wsRef = useRef(null);
    const searchContainerRef = useRef(null);

    // Click ra ngoài để đóng suggestions
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Lấy danh sách cổ phiếu
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

    // Lọc danh sách
    useEffect(() => {
        const filtered = stocks.filter(
            (s) =>
                s.stock_symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                s.stock_name.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setFilteredStocks(filtered);
    }, [searchQuery, stocks]);

    // WebSocket realtime
    useEffect(() => {
    if (predictionType !== "realtime" || !selectedStock) return;

    // Nếu WS cũ tồn tại, đóng trước khi mở WS mới cho stock khác
    if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
    }

    const ws = new WebSocket(
        `ws://localhost:8000/prediction/ws/realtime/predict/${selectedStock.stock_symbol}`
    );
    wsRef.current = ws;

    ws.onopen = () => console.log("WS connected for", selectedStock.stock_symbol);
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.prediction !== undefined) {
                setPredictions(prev => [...prev, data.prediction]);
            }
        } catch (err) {
            console.error("WS parse error", err);
        }
    };
    ws.onclose = () => console.log("WS closed for", selectedStock.stock_symbol);
    ws.onerror = (err) => console.error("WS error", err);

    // Cleanup chỉ khi component unmount
    return () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };
}, [selectedStock]); // Chỉ phụ thuộc vào stock, type realtime mặc định


    // Chọn stock
    const handleSelectStock = async (stock) => {
        setSelectedStock(stock);
        setSearchQuery(`${stock.stock_symbol} - ${stock.stock_name}`);
        setShowSuggestions(false);

        try {
            const infoRes = await axios.get(
                `http://localhost:8000/visualization/info/${stock.stock_symbol}`
            );
            setStockInfo(infoRes.data);
        } catch (err) {
            console.error("Lỗi lấy thông tin cổ phiếu:", err);
        }

        try {
            const histRes = await axios.get(
                `http://localhost:8000/visualization/ohlcv/${stock.stock_symbol}`
            );
            setHistoricalData(histRes.data.ohlc);
        } catch (err) {
            console.error("Lỗi lấy dữ liệu lịch sử:", err);
        }

        if (predictionType !== "realtime") {
            await fetchPrediction(stock.stock_symbol, predictionType);
        } else {
            setPredictions([]);
        }
    };

    // Lấy dự đoán REST cho các loại khác
    const fetchPrediction = async (symbol, type) => {
        setLoading(true);
        try {
            const endpoint = `http://localhost:8000/prediction/${type}/${symbol}`;
            const res = await axios.get(endpoint);
            setPredictions(res.data.predictions);
        } catch (err) {
            console.error("Lỗi lấy dự đoán:", err);
            alert("Không thể lấy dự đoán. Vui lòng thử lại!");
        } finally {
            setLoading(false);
        }
    };

    // Thay đổi loại dự đoán
    const handlePredictionTypeChange = async (type) => {
        setPredictionType(type);
        if (type !== "realtime" && selectedStock) {
            await fetchPrediction(selectedStock.stock_symbol, type);
        } else if (type === "realtime") {
            setPredictions([]);
        }
    };

    // Chuyển dữ liệu ngày -> tháng
    const convertDailyToMonthly = (dailyData) => {
        const monthlyMap = {};
        dailyData.forEach((item) => {
            const yearMonth = item.date.substring(0, 7);
            if (!monthlyMap[yearMonth]) monthlyMap[yearMonth] = { date: yearMonth, prices: [], volumes: [] };
            monthlyMap[yearMonth].prices.push(item.close_price);
            if (item.volumes) monthlyMap[yearMonth].volumes.push(item.volumes);
        });
        return Object.values(monthlyMap)
            .map((month) => ({
                date: month.date,
                close_price: month.prices.reduce((a, b) => a + b, 0) / month.prices.length,
                volumes: month.volumes.length > 0 ? month.volumes.reduce((a, b) => a + b, 0) / month.volumes.length : 0,
            }))
            .sort((a, b) => a.date.localeCompare(b.date));
    };

    // Chuẩn bị dữ liệu chart
    const getChartData = () => {
        if (!selectedStock || predictions.length === 0) return null;
        let historicalDates, historicalPrices;
        const isMonthly = predictionType === "medium-term" || predictionType === "long-term";

        if (isMonthly) {
            const monthlyData = convertDailyToMonthly(historicalData).slice(-24);
            historicalDates = monthlyData.map((d) => d.date);
            historicalPrices = monthlyData.map((d) => d.close_price);
        } else {
            const last60 = historicalData.slice(-60);
            historicalDates = last60.map((d) => d.date);
            historicalPrices = last60.map((d) => d.close_price);
        }

        const predictionLabels = predictions.map((_, idx) => {
            if (predictionType === "realtime") return `+${idx + 1}m`;
            if (predictionType === "short-term") return `+${idx + 1}d`;
            if (predictionType === "medium-term") return `+${idx + 1}M`;
            if (predictionType === "long-term") return `+${idx + 1}M`;
            return `+${idx + 1}`;
        });

        return {
            labels: [...historicalDates, ...predictionLabels],
            datasets: [
                {
                    label: isMonthly ? "Giá lịch sử (theo tháng)" : "Giá lịch sử (theo ngày)",
                    data: [...historicalPrices, ...Array(predictions.length).fill(null)],
                    borderColor: "rgb(75, 192, 192)",
                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                    tension: 0.1,
                },
                {
                    label: "Dự đoán",
                    data: [...Array(historicalDates.length).fill(null), ...predictions],
                    borderColor: "rgb(255, 99, 132)",
                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                    borderDash: [5, 5],
                    tension: 0.1,
                },
            ],
        };
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: "top", labels: { color: "#e2e8f0" } },
            title: {
                display: true,
                text: `Biểu đồ dự đoán giá ${selectedStock ? selectedStock.stock_symbol : ""}`,
                color: "#e2e8f0",
            },
        },
        scales: {
            y: { ticks: { color: "#a0aec0" }, grid: { color: "#2d3748" } },
            x: { ticks: { color: "#a0aec0" }, grid: { color: "#2d3748" } },
        },
    };

    return (
        <div className="pred-page">
            <header className="pred-header">
                <h1>Dự đoán giá cổ phiếu</h1>
                <div className="search-container" ref={searchContainerRef}>
                    <input
                        type="text"
                        placeholder="Tìm kiếm mã hoặc tên cổ phiếu..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => setShowSuggestions(true)}
                        className="search-input"
                    />
                    {showSuggestions && filteredStocks.length > 0 && (
                        <ul className="suggestions-list">
                            {filteredStocks.slice(0, 10).map((stock) => (
                                <li key={stock.stock_symbol} onClick={() => handleSelectStock(stock)} className="suggestion-item">
                                    <strong>{stock.stock_symbol}</strong> - {stock.stock_name}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </header>

            {stockInfo && (
                <div className="stock-info">
                    <h2>{stockInfo.stock_name} ({stockInfo.stock_symbol})</h2>
                    <p>Ngành: {stockInfo.major} | Sàn: {stockInfo.market_name}</p>
                </div>
            )}

            <div className="prediction-options">
                {["realtime", "short-term", "medium-term", "long-term"].map((type) => (
                    <button
                        key={type}
                        className={predictionType === type ? "active" : ""}
                        onClick={() => handlePredictionTypeChange(type)}
                        disabled={!selectedStock || loading}
                    >
                        {type === "realtime" && "Realtime (5 phút)"}
                        {type === "short-term" && "Ngắn hạn (15 ngày)"}
                        {type === "medium-term" && "Trung hạn (5 tháng)"}
                        {type === "long-term" && "Dài hạn (12 tháng)"}
                    </button>
                ))}
            </div>

            {loading && <div className="loading">Đang tải dự đoán...</div>}

            {!loading && predictions.length > 0 && (
                <div className="chart-container">
                    <Line data={getChartData()} options={chartOptions} />
                </div>
            )}

            {!loading && predictions.length > 0 && (
                <div className="predictions-table">
                    <h3>Chi tiết dự đoán</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Kỳ</th>
                                <th>Giá dự đoán (VNĐ)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {predictions.map((pred, idx) => (
                                <tr key={idx}>
                                    <td>
                                        {predictionType === "realtime" && `Phút thứ ${idx + 1}`}
                                        {predictionType === "short-term" && `Ngày ${idx + 1}`}
                                        {predictionType === "medium-term" && `Tháng ${idx + 1}`}
                                        {predictionType === "long-term" && `Tháng ${idx + 1}`}
                                    </td>
                                    <td>{pred.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PredPage;
