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

// Đăng ký các thành phần Chart.js
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
    
    // Tạo ref cho search container
    const searchContainerRef = useRef(null);

    // Xử lý click ra ngoài
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        };

        // Thêm event listener
        document.addEventListener("mousedown", handleClickOutside);
        
        // Cleanup
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    // Lấy danh sách cổ phiếu từ backend
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

    // Xử lý chọn cổ phiếu từ gợi ý
    const handleSelectStock = async (stock) => {
        setSelectedStock(stock);
        setSearchQuery(`${stock.stock_symbol} - ${stock.stock_name}`);
        setShowSuggestions(false);
        
        // Lấy thông tin chi tiết cổ phiếu
        try {
            const infoRes = await axios.get(`http://localhost:8000/visualization/info/${stock.stock_symbol}`);
            setStockInfo(infoRes.data);
        } catch (err) {
            console.error("Lỗi lấy thông tin cổ phiếu:", err);
        }

        // Lấy dữ liệu lịch sử theo ngày
        try {
            const histRes = await axios.get(`http://localhost:8000/visualization/ohlcv/${stock.stock_symbol}`);
            setHistoricalData(histRes.data.ohlc);
        } catch (err) {
            console.error("Lỗi lấy dữ liệu lịch sử:", err);
        }

        // Tự động dự đoán với loại hiện tại
        await fetchPrediction(stock.stock_symbol, predictionType);
    };

    // Lấy dự đoán từ backend
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

    // Xử lý thay đổi loại dự đoán
    const handlePredictionTypeChange = async (type) => {
        setPredictionType(type);
        if (selectedStock) {
            await fetchPrediction(selectedStock.stock_symbol, type);
        }
    };

    // Hàm chuyển đổi dữ liệu ngày sang tháng
    const convertDailyToMonthly = (dailyData) => {
        const monthlyMap = {};
        
        dailyData.forEach(item => {
            // Lấy năm-tháng từ date (format: YYYY-MM-DD)
            const yearMonth = item.date.substring(0, 7); // "2024-01"
            
            if (!monthlyMap[yearMonth]) {
                monthlyMap[yearMonth] = {
                    date: yearMonth,
                    prices: [],
                    volumes: []
                };
            }
            
            monthlyMap[yearMonth].prices.push(item.close_price);
            if (item.volumes) {
                monthlyMap[yearMonth].volumes.push(item.volumes);
            }
        });
        
        // Tính giá trung bình cho mỗi tháng
        return Object.values(monthlyMap).map(month => ({
            date: month.date,
            close_price: month.prices.reduce((a, b) => a + b, 0) / month.prices.length,
            volumes: month.volumes.length > 0 
                ? month.volumes.reduce((a, b) => a + b, 0) / month.volumes.length 
                : 0
        })).sort((a, b) => a.date.localeCompare(b.date));
    };

    // Chuẩn bị dữ liệu cho biểu đồ
    const getChartData = () => {
        if (!selectedStock || predictions.length === 0) return null;

        let historicalDates, historicalPrices;
        
        // Xác định xem có cần dữ liệu theo tháng không
        const isMonthlyPrediction = predictionType === "medium-term" || predictionType === "long-term";
        
        if (isMonthlyPrediction) {
            // Chuyển đổi dữ liệu ngày sang tháng
            const monthlyData = convertDailyToMonthly(historicalData);
            // Lấy nhiều tháng hơn để biểu đồ có ý nghĩa (24 tháng = 2 năm)
            const historicalMonths = monthlyData.slice(-24);
            historicalDates = historicalMonths.map((d) => d.date);
            historicalPrices = historicalMonths.map((d) => d.close_price);
        } else {
            // Sử dụng dữ liệu theo ngày (60 ngày)
            const historicalLast60 = historicalData.slice(-60);
            historicalDates = historicalLast60.map((d) => d.date);
            historicalPrices = historicalLast60.map((d) => d.close_price);
        }

        // Tạo nhãn cho dự đoán
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
                    label: isMonthlyPrediction ? "Giá lịch sử (theo tháng)" : "Giá lịch sử (theo ngày)",
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
            legend: {
                position: "top",
                labels: {
                    color: "#e2e8f0"
                }
            },
            title: {
                display: true,
                text: `Biểu đồ dự đoán giá ${selectedStock ? selectedStock.stock_symbol : ""}`,
                color: "#e2e8f0"
            },
        },
        scales: {
            y: {
                beginAtZero: false,
                ticks: {
                    color: "#a0aec0"
                },
                grid: {
                    color: "#2d3748"
                }
            },
            x: {
                ticks: {
                    color: "#a0aec0"
                },
                grid: {
                    color: "#2d3748"
                }
            }
        },
    };

    return (
        <div className="pred-page">
            {/* Header với thanh tìm kiếm */}
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
                                <li
                                    key={stock.stock_symbol}
                                    onClick={() => handleSelectStock(stock)}
                                    className="suggestion-item"
                                >
                                    <strong>{stock.stock_symbol}</strong> - {stock.stock_name}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </header>

            {/* Thông tin cổ phiếu */}
            {stockInfo && (
                <div className="stock-info">
                    <h2>{stockInfo.stock_name} ({stockInfo.stock_symbol})</h2>
                    <p>Ngành: {stockInfo.major} | Sàn: {stockInfo.market_name}</p>
                </div>
            )}

            {/* Các nút chọn loại dự đoán */}
            <div className="prediction-options">
                <button
                    className={predictionType === "realtime" ? "active" : ""}
                    onClick={() => handlePredictionTypeChange("realtime")}
                    disabled={!selectedStock || loading}
                >
                    Realtime (5 phút)
                </button>
                <button
                    className={predictionType === "short-term" ? "active" : ""}
                    onClick={() => handlePredictionTypeChange("short-term")}
                    disabled={!selectedStock || loading}
                >
                    Ngắn hạn (15 ngày)
                </button>
                <button
                    className={predictionType === "medium-term" ? "active" : ""}
                    onClick={() => handlePredictionTypeChange("medium-term")}
                    disabled={!selectedStock || loading}
                >
                    Trung hạn (5 tháng)
                </button>
                <button
                    className={predictionType === "long-term" ? "active" : ""}
                    onClick={() => handlePredictionTypeChange("long-term")}
                    disabled={!selectedStock || loading}
                >
                    Dài hạn (12 tháng)
                </button>
            </div>

            {/* Hiển thị loading */}
            {loading && <div className="loading">Đang tải dự đoán...</div>}

            {/* Biểu đồ */}
            {!loading && predictions.length > 0 && (
                <div className="chart-container">
                    <Line data={getChartData()} options={chartOptions} />
                </div>
            )}

            {/* Bảng kết quả dự đoán */}
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