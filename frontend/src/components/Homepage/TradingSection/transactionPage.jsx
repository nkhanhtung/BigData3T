import './transactionPage.css';
import { useEffect, useState } from "react";
import TradeRequestFrame from "./tradeRequestFrame";
import ChartFrame from "./ChartFrame";
import OrderHistoryFrame from "./orderHistoryFrame";

const TransactionPage = () => {
    const [selectedStock, setSelectedStock] = useState(null);

    return (
        <div className='transaction-layout'>
            <div className='left-panel'>
                <TradeRequestFrame
                    selectedStock={selectedStock}
                    setSelectedStock={setSelectedStock}
                />
            </div>

            <div className='right-panel'>
                <div className='section-block'>
                    <ChartFrame stockSymbol={selectedStock} />
                </div>

                <div className='section-block'>
                    <OrderHistoryFrame />
                </div>
            </div>
        </div>
    )
}

export default TransactionPage;