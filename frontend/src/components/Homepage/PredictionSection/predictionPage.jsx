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

    const [historicalData, setHistoricalData] = useState([]);
    const [stockInfo, setStockInfo] = useState(null);
    const [loading, setLoading] = useState(false);

    const [realtimePredictions, setRealtimePredictions] = useState([]);
    const [staticPredictions, setStaticPredictions] = useState([]);

    const wsRef = useRef(null);
    const searchContainerRef = useRef(null);

    // Fetch stock list
    useEffect(() => {
        axios.get("http://localhost:8000/visualization/stocks/list")
            .then((res) => {
                setStocks(res.data.stocks);
                setFilteredStocks(res.data.stocks);
            })
            .catch((err) => console.error("Error fetching stocks:", err));
    }, []);

    // Filter stocks
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

        if (wsRef.current) wsRef.current.close();

        const ws = new WebSocket(
            `ws://localhost:8000/prediction/ws/realtime/predict/${selectedStock.stock_symbol}`
        );
        wsRef.current = ws;

        ws.onopen = () => console.log("Realtime WS connected");
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.historical !== undefined && historicalData.length === 0) {
                // data.historical là giá thực tế tiếp theo
                setHistoricalData((prev) => [...prev, ...data.historical].slice(0, 60));
            }
            if (data.prediction !== undefined) {
                setRealtimePredictions((prev) => [...prev, data.prediction]);
            }
            if (data.real !== undefined) {
                const fixedReal = {
                    ...data.real,
                    date: typeof data.real.date === "number"
                        ? new Date(data.real.date * 1000).toISOString()
                        : data.real.date,
                };

                setHistoricalData((prev) => {
                    const normalized = prev.map(d => ({
                        ...d,
                        date: typeof d.date === "number"
                            ? new Date(d.date * 1000).toISOString()
                            : d.date,
                    }));

                    return [...normalized, fixedReal].slice(-60);
                });
            }


        };

        return () => ws.close();
    }, [selectedStock, predictionType]);

    // Select stock
    const handleSelectStock = async (stock) => {
        setSelectedStock(stock);
        setShowSuggestions(false);
        setSearchQuery(`${stock.stock_symbol} - ${stock.stock_name}`);

        // Fetch stock info
        const info = await axios.get(`http://localhost:8000/visualization/info/${stock.stock_symbol}`);
        setStockInfo(info.data);

        // Load historical data
        if (predictionType === "realtime") {
            const hist = await axios.get(
                `http://localhost:8000/visualization/ohlcv_1p/${stock.stock_symbol}`
            );
            console.log("historicalData realtime:", hist.data.ohlc);
            setHistoricalData(hist.data.ohlc || []);
        } else {
            const hist = await axios.get(
                `http://localhost:8000/visualization/ohlcv/${stock.stock_symbol}`
            );
            setHistoricalData(hist.data.ohlc || []);
        }

        // Reset predictions
        setRealtimePredictions([]);
        setStaticPredictions([]);

        if (predictionType !== "realtime") {
            await fetchPrediction(stock.stock_symbol, predictionType);
        }
    };

    // Fetch static prediction
    const fetchPrediction = async (symbol, type) => {
        setLoading(true);
        try {
            const res = await axios.get(
                `http://localhost:8000/prediction/${type}/${symbol}`
            );
            setStaticPredictions(res.data.predictions || []);
        } catch {
            alert("Không thể lấy dự đoán!");
        } finally {
            setLoading(false);
        }
    };

    // Change prediction type
    const handlePredictionTypeChange = async (type) => {
        setPredictionType(type);
        setRealtimePredictions([]);
        setStaticPredictions([]);

        if (!selectedStock) return;

        if (type === "realtime") {
            const hist = await axios.get(
                `http://localhost:8000/visualization/ohlcv_1p/${selectedStock.stock_symbol}`
            );
            setHistoricalData(hist.data.ohlc || []);
        } else {
            const hist = await axios.get(
                `http://localhost:8000/visualization/ohlcv/${selectedStock.stock_symbol}`
            );
            setHistoricalData(hist.data.ohlc || []);
            await fetchPrediction(selectedStock.stock_symbol, type);
        }
    };

    // Prepare chart data
    const [chartData, setChartData] = useState({ labels: [], datasets: [] });

    const [predictionTimes, setPredictionTimes] = useState([]);

    // ... import và code cũ

    // Thay thế useEffect tính chartData bằng đoạn này:
    // ... import và code cũ

    // Thay thế toàn bộ useEffect tính chartData bằng đoạn này:
    useEffect(() => {
        if (!selectedStock || historicalData.length === 0) return;

        const preds = predictionType === "realtime" ? realtimePredictions : staticPredictions;
        const slicedHistory = historicalData.slice(-60);

        // --- HÀM FORMAT THÔNG MINH HƠN ---
        const formatLabel = (dateInput) => {
            const str = String(dateInput);
            
            if (predictionType === "realtime") {
                // Realtime: Cắt lấy GIỜ PHÚT (HH:mm) -> vị trí 11 đến 16
                // Ví dụ: "2023-12-01T10:15:00" -> "10:15"
                return str.substring(11, 16);
            } else {
                // Các loại hạn khác: Cắt lấy NGÀY THÁNG (YYYY-MM-DD) -> vị trí 0 đến 10
                // Ví dụ: "2023-12-01T00:00:00" -> "2023-12-01"
                return str.substring(0, 10);
            }
        };

        // 1. Tạo trục X (Labels) từ dữ liệu lịch sử
        const labels = slicedHistory.map(d => formatLabel(d.date));
        
        // 2. Dữ liệu giá thực tế
        const historicalPrices = slicedHistory.map(d => d.close_price ?? d);

        // 3. Xử lý dữ liệu dự đoán
        let predictionData = [];

        if (predictionType === "realtime") {
            // Realtime: Overlay (Đè lên)
            const emptyCount = Math.max(0, historicalPrices.length - preds.length);
            predictionData = [
                ...Array(emptyCount).fill(null), 
                ...preds 
            ];
            predictionData = predictionData.slice(-historicalPrices.length);

        } else {
            // Short/Medium/Long-term: Vẽ nối tiếp tương lai
            const isMonthly = predictionType === "medium-term" || predictionType === "long-term";
            
            // Tính toán ngày tương lai để hiển thị label cho phần dự đoán
            // Lấy ngày cuối cùng của lịch sử để cộng thêm
            const lastHistoryDateStr = slicedHistory[slicedHistory.length - 1].date; 
            const lastDate = new Date(lastHistoryDateStr); 

            const futureLabels = preds.map((_, idx) => {
                const nextDate = new Date(lastDate);
                
                if (isMonthly) {
                     // Nếu là monthly thì cộng tháng
                    nextDate.setMonth(nextDate.getMonth() + (idx + 1));
                } else {
                    // Nếu là daily thì cộng ngày
                    nextDate.setDate(nextDate.getDate() + (idx + 1));
                }
                
                // Format ngày tương lai về dạng YYYY-MM-DD cho đồng bộ với trục X
                return nextDate.toISOString().slice(0, 10);
            });

            // Nối label tương lai vào trục X
            labels.push(...futureLabels);
            
            // Nối dữ liệu dự đoán vào sau dữ liệu lịch sử
            predictionData = [...Array(historicalPrices.length).fill(null), ...preds];
        }

        // Cập nhật Chart
        setChartData({
            labels: labels,
            datasets: [
                {
                    label: "Giá thực tế",
                    data: historicalPrices,
                    borderColor: "rgb(75, 192, 192)",
                    pointRadius: 2,
                    tension: 0.1,
                    order: 1,
                },
                {
                    label: "Dự đoán",
                    data: predictionData,
                    borderColor: "rgb(255, 99, 132)",
                    backgroundColor: "rgba(255, 99, 132, 0.5)",
                    pointRadius: 4,
                    // Nếu không phải realtime thì dùng điểm tròn bình thường cho dễ nhìn
                    pointStyle: predictionType === 'realtime' ? 'rectRot' : 'circle',
                    pointBorderWidth: 2,
                    tension: 0.1,
                    order: 0,
                },
            ],
        });
    }, [historicalData, realtimePredictions, staticPredictions, predictionType, selectedStock]);

    const displayPreds =
        predictionType === "realtime" ? realtimePredictions : staticPredictions;

    return (
        <div className="pred-page">
            <header className="pred-header">
                <h1>Dự đoán giá cổ phiếu</h1>

                <div className="search-container" ref={searchContainerRef}>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Tìm mã cổ phiếu..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => setShowSuggestions(true)}
                    />
                    {showSuggestions && filteredStocks.length > 0 && (
                        <ul className="suggestions-list">
                            {filteredStocks.slice(0, 10).map((stock) => (
                                <li
                                    key={stock.stock_symbol}
                                    className="suggestion-item"
                                    onClick={() => handleSelectStock(stock)}
                                >
                                    <strong>{stock.stock_symbol}</strong> - {stock.stock_name}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </header>

            {stockInfo && (
                <div className="stock-info">
                    <h2>
                        {stockInfo.stock_name} ({stockInfo.stock_symbol})
                    </h2>
                    <p>Ngành: {stockInfo.major}</p>
                </div>
            )}

            <div className="prediction-options">
                {["realtime", "short-term", "medium-term", "long-term"].map((type) => (
                    <button
                        key={type}
                        className={predictionType === type ? "active" : ""}
                        onClick={() => handlePredictionTypeChange(type)}
                        disabled={!selectedStock}
                    >
                        {type === "realtime" && "Realtime (mỗi phút)"}
                        {type === "short-term" && "Ngắn hạn (15 ngày)"}
                        {type === "medium-term" && "Trung hạn (5 tháng)"}
                        {type === "long-term" && "Dài hạn (12 tháng)"}
                    </button>
                ))}
            </div>

            {loading && <div className="loading">Đang tải dự đoán...</div>}

            {!loading && historicalData.length > 0 && (
                <div className="chart-container">
                    <Line data={chartData} />
                </div>
            )}

            {!loading && displayPreds.length > 0 && (
                <div className="predictions-table">
                    <h3>Chi tiết dự đoán</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Kỳ</th>
                                <th>Giá dự đoán</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayPreds.map((v, idx) => (
                                <tr key={idx}>
                                    <td>{idx + 1}</td>
                                    <td>{v.toFixed(2)}</td>
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
