import { useEffect, useState, useMemo } from "react";
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
    const [period, setPeriod] = useState("day"); // day, week, month

    // Lấy data từ backend
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
            date: last.date, // Lấy ngày cuối của chu kỳ
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

        // Sắp xếp dữ liệu theo ngày tăng dần
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
                // Lấy tuần trong năm (ISO week)
                const startOfYear = new Date(date.getFullYear(), 0, 1);
                const weekNum = Math.ceil((((date - startOfYear) / 86400000) + startOfYear.getDay() + 1) / 7);
                periodKey = `${date.getFullYear()}-W${weekNum}`;
            } else if (period === "month") {
                // Lấy tháng-năm
                periodKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            }

            if (currentPeriodKey !== periodKey) {
                // Xử lý nhóm trước đó
                if (currentGroup.length > 0) {
                    aggregated.push(aggregateGroup(currentGroup));
                }
                // Bắt đầu nhóm mới
                currentGroup = [item];
                currentPeriodKey = periodKey;
            } else {
                currentGroup.push(item);
            }
        });

        // Xử lý nhóm cuối cùng
        if (currentGroup.length > 0) {
            aggregated.push(aggregateGroup(currentGroup));
        }

        return aggregated;
    }, [ohlcvData, period]);

    // Nếu chưa chọn mã cổ phiếu -> hiển thị khung trống lớn
    if (!stockSymbol) {
        return (
            <div className="empty-chart">
                <div className="empty-chart-text">Chưa chọn mã cổ phiếu</div>
            </div>
        );
    }

    // Nếu có mã mà chưa load data -> loading
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
                // max: now,
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