import { useEffect, useState } from "react";
import axios from "axios";
import './orderHistoryFrame.css'

const OrderHistory = () => {
    const [orders, setOrders] = useState([]);
    const [cancellingId, setCancellingId] = useState(null);
    const userId = sessionStorage.getItem("user_id");

    // Load danh sách lệnh
    const fetchOrders = async () => {
        try {
            const res = await axios.get(
                `http://localhost:8000/trading/user/${userId}`
            );
            setOrders(res.data);
        } catch (err) {
            console.error("Lỗi lấy lịch sử lệnh:", err);
        }
    };

    // Hủy lệnh
    const handleCancelOrder = async (orderId) => {
        setCancellingId(orderId);
        try {
            await axios.post(`http://localhost:8000/trading/${orderId}/cancel`);
            await fetchOrders();
        } catch (err) {
            console.error("Lỗi hủy lệnh:", err);
            alert(err.response?.data?.detail || "Không thể hủy lệnh. Vui lòng thử lại.");
        } finally {
            setCancellingId(null);
        }
    };

    // Kiểm tra lệnh có thể hủy được không
    const isCancellable = (status) => {
        return ["PENDING", "PARTIALLY_FILLED"].includes(status?.toUpperCase());
    };

    useEffect(() => {
        fetchOrders();
        // auto refresh mỗi 3 giây
        const interval = setInterval(fetchOrders, 3000);
        return () => clearInterval(interval);
    }, [userId]);

    return (
        <div className="order-history-frame">
            <h2 className="order-history-title">Lịch Sử Đặt Lệnh</h2>

            <table className="order-table">
                <thead>
                    <tr>
                        <th>Mã CP</th>
                        <th>Loại</th>
                        <th>Giá</th>
                        <th>Khối lượng</th>
                        <th>Trạng thái</th>
                        <th>Thời gian</th>
                    </tr>
                </thead>

                <tbody>
                    {orders.length === 0 ? (
                        <tr>
                            <td colSpan="6" className="empty-text">
                                Chưa có lệnh nào
                            </td>
                        </tr>
                    ) : (
                        orders.map(order => (
                            <tr key={order.order_id}>
                                <td>{order.stock_symbol}</td>

                                <td className={order.order_type === "BUY" ? "buy" : "sell"}>
                                    {order.order_type}
                                </td>

                                <td>{order.price.toLocaleString()}</td>
                                <td>{order.quantity.toLocaleString()}</td>

                                <td className={`status ${order.status.toLowerCase()}`}>
                                    {order.status}
                                </td>

                                <td>
                                    {new Date(order.created_timestamp).toLocaleString("vi-VN")}
                                </td>

                                <td>
                                    {isCancellable(order.status) ? (
                                        <button
                                            className="cancel-btn"
                                            onClick={() => handleCancelOrder(order.order_id)}
                                            disabled={cancellingId === order.order_id}
                                        >
                                            {cancellingId === order.order_id ? "Đang hủy..." : "Hủy"}
                                        </button>
                                    ) : (
                                        <span className="no-action"></span>
                                    )}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default OrderHistory;