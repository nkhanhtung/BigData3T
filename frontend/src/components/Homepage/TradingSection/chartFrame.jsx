import { useEffect, useState, useMemo, useRef } from "react";
import axios from "axios";
import './chartFrame.css';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, TimeScale, Tooltip, Legend } from "chart.js";
import { Chart } from "react-chartjs-2";
import { CandlestickController, CandlestickElement } from "chartjs-chart-financial";
import 'chartjs-adapter-date-fns';
import zoomPlugin from 'chartjs-plugin-zoom';

// --- Đăng ký Chart.js ---
ChartJS.register(
    CategoryScale, LinearScale, BarElement, LineElement, PointElement,
    TimeScale, Tooltip, Legend, CandlestickController, CandlestickElement, zoomPlugin
);

const ChartFrame = ({ stockSymbol }) => {
    const [infoData, setInfoData] = useState(null);
    const [ohlcvData, setOhlcvData] = useState([]);           // Dữ liệu lịch sử
    const [realtimeOhlcvData, setRealtimeOhlcvData] = useState([]); // Dữ liệu realtime
    const [activeTab, setActiveTab] = useState("overview");
    const [chartType, setChartType] = useState("candlestick");
    const [period, setPeriod] = useState("day");
    const wsRef = useRef(null);

    // --- WebSocket Real-time ---
    useEffect(() => {
        if (!stockSymbol) return;

        const ws = new WebSocket(`ws://localhost:8000/realtime/ws/realtime-ohlc/${stockSymbol}`);
        wsRef.current = ws;

        ws.onopen = () => console.log(`Connected to WS for ${stockSymbol}`);

        ws.onmessage = (event) => {
            try {
                const newData = JSON.parse(event.data);

                if (newData.stock_symbol === stockSymbol) {
                    const targetDateStr = "2025-11-28"; // Ép ngày realtime luôn là 28/11

                    setRealtimeOhlcvData(prev => {
                        if (prev.length === 0) {
                            // Tạo nến mới cho ngày 28/11
                            return [{
                                date: targetDateStr,
                                open_price: newData.open_price || newData.close_price,
                                high_price: newData.high_price || newData.close_price,
                                low_price: newData.low_price || newData.close_price,
                                close_price: newData.close_price,
                                volumes: newData.volumes || 0,
                                stock_symbol: stockSymbol
                            }];
                        } else {
                            // Cập nhật nến realtime hiện có
                            const current = prev[0];
                            return [{
                                ...current,
                                close_price: newData.close_price,
                                high_price: Math.max(current.high_price, newData.high_price || newData.close_price),
                                low_price: Math.min(current.low_price, newData.low_price || newData.close_price),
                                volumes: current.volumes + (newData.volumes || 0)
                            }];
                        }
                    });
                }
            } catch (err) {
                console.error("WebSocket message parse error:", err);
            }
        };

        ws.onerror = (err) => console.error("WebSocket error:", err);
        ws.onclose = () => console.log("WebSocket disconnected");

        return () => { 
            if (ws.readyState === WebSocket.OPEN) ws.close(); 
        };
    }, [stockSymbol]);

    // --- Fetch dữ liệu lịch sử ---
    useEffect(() => {
        if (!stockSymbol) return;

        const fetchData = async () => {
            try {
                const infoRes = await axios.get(`http://localhost:8000/visualization/info/${stockSymbol}`);
                const ohlcvRes = await axios.get(`http://localhost:8000/visualization/ohlcv/${stockSymbol}`);
                setInfoData(infoRes.data);

                const sortedData = (ohlcvRes.data.ohlc || []).sort((a, b) => new Date(a.date) - new Date(b.date));
                setOhlcvData(sortedData);
            } catch (err) {
                console.error("Error fetching dashboard data:", err);
            }
        };

        fetchData();
    }, [stockSymbol]);

    // --- Kết hợp dữ liệu lịch sử + realtime ---
    const combinedOhlcvData = useMemo(() => {
        return [...ohlcvData, ...realtimeOhlcvData].sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [ohlcvData, realtimeOhlcvData]);

    // --- Các phần còn lại giữ nguyên (aggregateData, chartData, chartOptions) ---
    const aggregateGroup = (group) => {
        const sorted = [...group].sort((a, b) => new Date(a.date) - new Date(b.date));
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

    const aggregateData = useMemo(() => {
        if (!combinedOhlcvData || combinedOhlcvData.length === 0) return [];
        if (period === "day") return combinedOhlcvData;

        const sorted = [...combinedOhlcvData].sort((a, b) => new Date(a.date) - new Date(b.date));
        const aggregated = [];
        let currentGroup = [], currentKey = null;

        sorted.forEach(item => {
            const date = new Date(item.date);
            let key = period === "week"
                ? `${date.getFullYear()}-W${Math.ceil((((date - new Date(date.getFullYear(),0,1))/86400000 + new Date(date.getFullYear(),0,1).getDay()+1)/7))}`
                : `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}`;

            if (key !== currentKey) {
                if (currentGroup.length > 0) aggregated.push(aggregateGroup(currentGroup));
                currentGroup = [item];
                currentKey = key;
            } else currentGroup.push(item);
        });

        if (currentGroup.length > 0) aggregated.push(aggregateGroup(currentGroup));
        return aggregated;
    }, [combinedOhlcvData, period]);

    // --- Chart.js data ---
    const chartData = useMemo(() => {
        if (!aggregateData || aggregateData.length === 0) return {};

        if (chartType === "candlestick") {
            return {
                datasets: [{
                    label: "OHLC",
                    data: aggregateData.map(d => ({
                        x: new Date(d.date).getTime(),
                        o: d.open_price,
                        h: d.high_price,
                        l: d.low_price,
                        c: d.close_price
                    })),
                    barPercentage: 0.85,
                    categoryPercentage: 0.9,
                    color: { up: 'rgba(0,200,5,1)', down: 'rgba(255,50,50,1)', unchanged:'rgba(100,100,100,1)' },
                    borderColor: { up: 'rgba(0,200,5,1)', down:'rgba(255,50,50,1)', unchanged:'rgba(100,100,100,1)' },
                    wickColor: { up:'rgba(0,200,5,1)', down:'rgba(255,50,50,1)', unchanged:'rgba(100,100,100,1)' }
                }]
            };
        } else if (chartType === "line") {
            return {
                labels: aggregateData.map(d => new Date(d.date).getTime()),
                datasets: [{ label: "Giá đóng cửa", data: aggregateData.map(d => d.close_price), borderColor:"#00E396", backgroundColor:"rgba(0,227,150,0.1)", tension:0.2, pointRadius:0 }]
            };
        } else if (chartType === "bar") {
            return {
                labels: aggregateData.map(d => new Date(d.date).getTime()),
                datasets: [{ label: "Khối lượng", data: aggregateData.map(d => d.volumes), backgroundColor:"#008FFB" }]
            };
        }
    }, [aggregateData, chartType]);

    const defaultStart = new Date();
    defaultStart.setMonth(defaultStart.getMonth() - 3);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            legend: { display: false },
            tooltip: { mode: 'index', intersect: false, callbacks: { title: ctx => new Date(ctx[0].parsed.x).toLocaleDateString('vi-VN') }},
            zoom: { pan:{enabled:true,mode:'x'}, zoom:{wheel:{enabled:true},pinch:{enabled:true},mode:'x'} }
        },
        scales: {
            x: { type:'time', time:{unit:period==='day'?'day':period==='week'?'week':'month', tooltipFormat:'dd/MM/yyyy', displayFormats:{day:'dd/MM'}}, min:defaultStart, ticks:{source:'auto',autoSkip:true,maxTicksLimit:10} },
            y: { beginAtZero:false, ticks:{ callback: val => val.toLocaleString() } }
        }
    };

    if (!stockSymbol) return <div className="empty-chart">Chưa chọn mã cổ phiếu</div>;
    if (!infoData) return <div className="empty-chart">Đang tải dữ liệu...</div>;

    return (
        <div className="stock-dashboard-frame" onClick={e=>e.stopPropagation()}>
            <div className="dashboard-header">
                <div>
                    <h2>{infoData.stock_symbol} ({infoData.market_name}) <span style={{color:'red',fontSize:'0.6em',verticalAlign:'middle'}}>● LIVE</span></h2>
                    <p style={{color:'#888'}}>{infoData.stock_name}</p>
                </div>
                <div style={{textAlign:'right'}}>
                    <h2 style={{color:'#00E396'}}>{combinedOhlcvData.length>0?combinedOhlcvData[combinedOhlcvData.length-1].close_price.toLocaleString():'-'}</h2>
                </div>
            </div>
            <div className="dashboard-tabs">
                <button className={activeTab==="overview"?"active":""} onClick={()=>setActiveTab("overview")}>Biểu đồ</button>
                <button className={activeTab==="info"?"active":""} onClick={()=>setActiveTab("info")}>Thông tin</button>
            </div>
            <div className="dashboard-body">
                <div className="dashboard-chart-area">
                    <div className="chart-frame-wrapper">
                        <div className="chart-toolbar">
                            <div className="period-dropdown">
                                <button className="toolbar-btn">Chu kỳ: {period==='day'?'Ngày':period==='week'?'Tuần':'Tháng'}</button>
                            </div>
                            <div className="chart-type-dropdown">
                                <button className="toolbar-btn" onClick={()=>setChartType(chartType==='candlestick'?'line':'candlestick')}>
                                    {chartType==='candlestick'?'Biểu đồ Nến':'Biểu đồ Đường'}
                                </button>
                            </div>
                        </div>
                        <div className="chart-container" style={{height:'400px'}}>
                            {aggregateData.length>0 &&
                                <Chart type={chartType==='candlestick'?'candlestick':chartType} data={chartData} options={chartOptions} />
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChartFrame;
