import { useEffect, useState, useMemo, useRef } from "react";
import axios from "axios";
import './chartFrame.css';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, TimeScale, Tooltip, Legend } from "chart.js";
import { Chart } from "react-chartjs-2";
import { CandlestickController, CandlestickElement } from "chartjs-chart-financial";
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';

// --- Đăng ký Chart.js ---
ChartJS.register( CategoryScale, LinearScale, BarElement, LineElement, PointElement, TimeScale, Tooltip, Legend, CandlestickController, CandlestickElement, zoomPlugin );

const ChartFrame = ({ stockSymbol }) => {
    const [infoData, setInfoData] = useState(null);
    const [ohlcvData, setOhlcvData] = useState([]);
    const [activeTab, setActiveTab] = useState("overview");
    const [chartType, setChartType] = useState("candlestick");
    const [period, setPeriod] = useState("day");
    const wsRef = useRef(null);

    // ========== WebSocket Real-time Connection ==========
    useEffect(() => {
        if (!stockSymbol) return;

        // Kết nối WebSocket
        const ws = new WebSocket("ws://localhost:8000/realtime/ws/candlestick-ohlc");
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("WebSocket connected for real-time OHLC updates");
        };

        ws.onmessage = (event) => {
            try {
                const newData = JSON.parse(event.data);
                console.log("Received real-time OHLC:", newData);
                console.log("Current stock:", stockSymbol);
                console.log("Match:", newData.stock_symbol === stockSymbol);

                // Kiểm tra nếu data là của cổ phiếu đang xem
                if (newData.stock_symbol === stockSymbol) {
                    console.log("Updating chart for", stockSymbol);
                    setOhlcvData(prevData => {
                        // Tìm xem ngày này đã tồn tại chưa
                        const existingIndex = prevData.findIndex(
                            item => item.date === newData.date
                        );

                        if (existingIndex !== -1) {
                            // Cập nhật dữ liệu ngày hiện tại
                            const updated = [...prevData];
                            updated[existingIndex] = {
                                ...updated[existingIndex],
                                close_price: newData.close_price,
                                high_price: Math.max(updated[existingIndex].high_price, newData.high_price),
                                low_price: Math.min(updated[existingIndex].low_price, newData.low_price),
                                volumes: updated[existingIndex].volumes + (newData.volumes || 0)
                            };
                            return updated;
                        } else {
                            // Thêm dữ liệu ngày mới
                            return [...prevData, {
                                date: newData.date,
                                open_price: newData.open_price,
                                close_price: newData.close_price,
                                high_price: newData.high_price,
                                low_price: newData.low_price,
                                volumes: newData.volumes || 0
                            }].sort((a, b) => 
                                new Date(a.date).getTime() - new Date(b.date).getTime()
                            );
                        }
                    });
                }
            } catch (err) {
                console.error("❌ Error parsing WebSocket message:", err);
            }
        };

        ws.onerror = (error) => {
            console.error("❌ WebSocket error:", error);
        };

        ws.onclose = () => {
            console.log("🔌 WebSocket disconnected");
        };

        // Cleanup khi component unmount hoặc stockSymbol thay đổi
        return () => {
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close();
            }
        };
    }, [stockSymbol]);

    // Lấy data ban đầu từ backend
    useEffect(() => {
        if (!stockSymbol) return;

        const fetchData = async () => {
            try {
                const infoRes = await axios.get(`http://localhost:8000/visualization/info/${stockSymbol}`);
                const ohlcvRes = await axios.get(`http://localhost:8000/visualization/ohlcv/${stockSymbol}`);
                setInfoData(infoRes.data);
                setOhlcvData(ohlcvRes.data.ohlc);
            } catch (err) {
                console.error("Lỗi lấy dữ liệu dashboard:", err);
            }
        };
        fetchData();
    }, [stockSymbol]);

    // --- Hàm tổng hợp dữ liệu trong 1 chu kỳ ---
    const aggregateGroup = (group) => {
        const sorted = group.sort((a, b) => 
            new Date(a.date).getTime() - new Date(b.date).getTime()
        );

        const first = sorted[0];
        const last = sorted[sorted.length - 1];

        return {
            date: last.date,
            open_price: first.open_price,
            close_price: last.close_price,
            high_price: Math.max(...sorted.map(d => d.high_price)),
            low_price: Math.min(...sorted.map(d => d.low_price)),
            volumes: sorted.reduce((sum, d) => sum + d.volumes, 0)
        };
    };

    // --- Hàm chuyển đổi dữ liệu theo chu kỳ ---
    const aggregateData = useMemo(() => {
        if (!ohlcvData || ohlcvData.length === 0) return [];

        if (period === "day") {
            return ohlcvData;
        }

        const sortedData = [...ohlcvData].sort((a, b) => 
            new Date(a.date).getTime() - new Date(b.date).getTime()
        );

        const aggregated = [];
        let currentGroup = [];
        let currentPeriodKey = null;

        sortedData.forEach((item) => {
            const date = new Date(item.date);
            let periodKey;

            if (period === "week") {
                const startOfYear = new Date(date.getFullYear(), 0, 1);
                const weekNum = Math.ceil((((date - startOfYear) / 86400000) + startOfYear.getDay() + 1) / 7);
                periodKey = `${date.getFullYear()}-W${weekNum}`;
            } else if (period === "month") {
                periodKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            }

            if (currentPeriodKey !== periodKey) {
                if (currentGroup.length > 0) {
                    aggregated.push(aggregateGroup(currentGroup));
                }
                currentGroup = [item];
                currentPeriodKey = periodKey;
            } else {
                currentGroup.push(item);
            }
        });

        if (currentGroup.length > 0) {
            aggregated.push(aggregateGroup(currentGroup));
        }

        return aggregated;
    }, [ohlcvData, period]);

    if (!stockSymbol) {
        return (
            <div className="empty-chart">
                <div className="empty-chart-text">Chưa chọn mã cổ phiếu</div>
            </div>
        );
    }

    if (!infoData) {
        return (
            <div className="empty-chart">
                <div className="empty-chart-text">Đang tải dữ liệu...</div>
            </div>
        );
    }

    // --- Chuẩn bị dữ liệu cho Chart.js ---
    const chartData = () => {
        const data = aggregateData;
        if (!data || data.length === 0) return {};

        if (chartType === "candlestick") {
            const dataPoints = data.map(d => ({
                x: new Date(d.date).getTime(),
                o: d.open_price,
                h: d.high_price,
                l: d.low_price,
                c: d.close_price
            }));

            return {
                datasets: [
                    {
                        label: "OHLC",
                        data: dataPoints,
                        barPercentage: 0.85,
                        categoryPercentage: 0.9,
                    }
                ]
            };
        } else if (chartType === "line") {
            return {
                labels: data.map(d => new Date(d.date).getTime()),
                datasets: [
                    {
                        label: "Giá đóng cửa",
                        data: data.map(d => d.close_price),
                        borderColor: "springgreen",
                        backgroundColor: "rgba(0,255,0,0.1)",
                        tension: 0.2
                    }
                ]
            };
        } else if (chartType === "bar") {
            return {
                labels: data.map(d => new Date(d.date).getTime()),
                datasets: [
                    {
                        label: "Khối lượng",
                        data: data.map(d => d.volumes),
                        backgroundColor: "skyblue",
                    }
                ]
            };
        }
    };

    const now = new Date();
    const defaultStart = new Date();
    defaultStart.setMonth(now.getMonth() - 6);

    // --- Options Chart ---
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 750 // Hiệu ứng mượt mà khi cập nhật
        },
        plugins: {
            legend: { display: true },
            tooltip: { 
                mode: 'index', 
                intersect: false,
                callbacks: {
                    title: (context) => {
                        const date = new Date(context[0].parsed.x);
                        return date.toLocaleDateString('vi-VN');
                    }
                }
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x'
                },
                zoom: {
                    wheel: { enabled: true },
                    pinch: { enabled: true },
                    mode: 'x'
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: { 
                    unit: period === 'day' ? 'day' : period === 'week' ? 'week' : 'month',
                    tooltipFormat: 'dd/MM/yyyy' 
                },
                min: defaultStart,
                ticks: { maxTicksLimit: 20, autoSkip: true }
            },
            y: {
                beginAtZero: false,
                ticks: { precision: 0 }
            }
        }
    };

    return (
        <div className="stock-dashboard-frame" onClick={(e) => e.stopPropagation()}>
            {/* HEADER */}
            <div className="dashboard-header">
                <div>
                    <h2>
                        {infoData.stock_symbol} ({infoData.market_name})
                        <span className="live-indicator" title="Cập nhật real-time">🔴 LIVE</span>
                    </h2>
                    <p>{infoData.stock_name}</p>
                </div>
                <button className="btn-chart">Xem phân tích chi tiết</button>
            </div>

            {/* TAB MENU */}
            <div className="dashboard-tabs">
                <button className={activeTab === "overview" ? "active" : ""} onClick={() => setActiveTab("overview")}>Tổng quan</button>
                <button className={activeTab === "info" ? "active" : ""} onClick={() => setActiveTab("info")}>Thông tin</button>
            </div>

            {/* CHART */}
            <div className="dashboard-body">
                <div className="dashboard-chart-area">
                    <div className="chart-frame-wrapper">
                        <div className="chart-toolbar">
                            <div className="period-dropdown">
                                <button>Chu kỳ: {period === 'day' ? '1 Ngày' : period === 'week' ? '1 Tuần' : '1 Tháng'}</button>
                                <div className="dropdown-content">
                                    <button onClick={() => setPeriod("day")}>1 Ngày</button>
                                    <button onClick={() => setPeriod("week")}>1 Tuần</button>
                                    <button onClick={() => setPeriod("month")}>1 Tháng</button>
                                </div>
                            </div>
                            <button>Chỉ báo</button>
                            <div className="chart-type-dropdown">
                                <button>Loại: {chartType === 'candlestick' ? 'Nến' : chartType === 'line' ? 'Đường' : 'Cột'}</button>
                                <div className="dropdown-content">
                                    <button onClick={() => setChartType("candlestick")}>Biểu đồ nến</button>
                                    <button onClick={() => setChartType("line")}>Đường thẳng</button>
                                    <button onClick={() => setChartType("bar")}>Biểu đồ cột</button>
                                </div>
                            </div>
                        </div>
                        <div className="chart-container">
                            {aggregateData.length > 0 && (
                                <Chart
                                    type={chartType === "candlestick" ? "candlestick" : chartType}
                                    data={chartData()}
                                    options={chartOptions}
                                />
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChartFrame;