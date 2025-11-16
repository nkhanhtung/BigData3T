import NavigationBar from './navigation_bar';
import MarketPage from './MarketSection/marketPage';
import ChartPage from './ChartSection/chartPage';
import './homepage.css';
import { Routes, Route } from 'react-router-dom';

export default function App() {
    return (
        <div className="homepage-container">
            <NavigationBar />
            <div className='homepage-container-main'>
                {/* Hiển thị nội dung trang tương ứng */}
                <Routes>
                    <Route path="market" element={<MarketPage />} />
                    <Route path="chart" element={<ChartPage />} />
                    {/* Mặc định vào /homepage sẽ vào market */}
                    <Route path="/" element={<MarketPage />} />
                </Routes>
            </div>
        </div>
    );
}