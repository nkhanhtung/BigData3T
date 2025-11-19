import { useEffect, useState } from "react";
import axios from "axios";
import './stockDashboardOverlay.css';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, TimeScale, Tooltip, Legend } from "chart.js";
import { Chart } from "react-chartjs-2";
import { CandlestickController, CandlestickElement } from "chartjs-chart-financial";
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';

// --- Đăng ký Chart.js ---
ChartJS.register( CategoryScale, LinearScale, BarElement, LineElement, PointElement, TimeScale, Tooltip, Legend, CandlestickController, CandlestickElement, zoomPlugin );

const StockDashboardOverlay = ({ stockSymbol, onClose }) => {
    const [infoData, setInfoData] = useState(null);
    const [ohlcvData, setOhlcvData] = useState([]);
    const [activeTab, setActiveTab] = useState("overview");
    const [chartType, setChartType] = useState("candlestick"); // mặc định nến

    // --- Fetch data từ backend ---
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

    // --- Debug: kiểm tra date ---
    useEffect(() => {
        if (ohlcvData.length > 0) {
            console.log("Kiểm tra 20 date đầu:", ohlcvData.map(d => d.date).slice(0, 20));
        }
    }, [ohlcvData]);

    if (!infoData) return null;

    // --- Chuẩn bị dữ liệu cho Chart.js ---
    const chartData = () => {
        if (!ohlcvData || ohlcvData.length === 0) return {};

        if (chartType === "candlestick") {
            const dataPoints = ohlcvData.map(d => ({
                x: new Date(d.date).getTime(), // timestamp
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
                        barPercentage: 0.85,      // giảm width nến
                        categoryPercentage: 0.9, // tránh chồng nhau
                    }
                ]
            };
        } else if (chartType === "line") {
            return {
                labels: ohlcvData.map(d => new Date(d.date).getTime()),
                datasets: [
                    {
                        label: "Giá đóng cửa",
                        data: ohlcvData.map(d => d.close_price),
                        borderColor: "springgreen",
                        backgroundColor: "rgba(0,0,255,0.1)",
                        tension: 0.2
                    }
                ]
            };
        } else if (chartType === "bar") {
            return {
                labels: ohlcvData.map(d => new Date(d.date).getTime()),
                datasets: [
                    {
                        label: "Khối lượng",
                        data: ohlcvData.map(d => d.volumes),
                        backgroundColor: "skyblue",
                    }
                ]
            };
        }
    };

    const now = new Date();
    const defaultStart = new Date();
    defaultStart.setMonth(now.getMonth() - 6); // 6 tháng trước
    // --- Options Chart ---
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: true },
            tooltip: { mode: 'index', intersect: false },
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
                time: { unit: 'day', tooltipFormat: 'dd/MM/yyyy' },
                min: defaultStart,  // chỉ hiện 6 tháng gần nhất
                max: now,           // tới hôm nay
                ticks: { maxTicksLimit: 20, autoSkip: true }
            },
            y: {
                beginAtZero: false,
                ticks: { precision: 0 }
            }
        }
    };

    return (
        <div className="stock-dashboard-overlay" onClick={onClose}>
            <div className="stock-dashboard-box" onClick={(e) => e.stopPropagation()}>
                {/* HEADER */}
                <div className="dashboard-header">
                    <div>
                        <h2>{infoData.stock_symbol} ({infoData.market_name})</h2>
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
                        <div className="chart-toolbar">
                            <button>Chu kỳ</button>
                            <button>Chỉ báo</button>
                            <div className="chart-type-dropdown">
                                <button>Loại biểu đồ</button>
                                <div className="dropdown-content">
                                    <button onClick={() => setChartType("candlestick")}>Biểu đồ nến</button>
                                    <button onClick={() => setChartType("line")}>Đường thẳng</button>
                                    <button onClick={() => setChartType("bar")}>Biểu đồ cột</button>
                                </div>
                            </div>
                        </div>
                        <div className="chart-container">
                            {ohlcvData.length > 0 && (
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

export default StockDashboardOverlay;