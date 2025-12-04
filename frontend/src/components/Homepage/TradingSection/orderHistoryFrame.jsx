import { useEffect, useState } from "react";
import axios from "axios";
import './orderHistoryFrame.css'

const OrderHistory = () => {
    const [orders, setOrders] = useState([]);
    const [cancellingId, setCancellingId] = useState(null);

    const [showConfirm, setShowConfirm] = useState(false);
    const [orderToCancel, setOrderToCancel] = useState(null);

    const userId = sessionStorage.getItem("user_id");

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

    const openConfirmCancel = (orderId) => {
        setOrderToCancel(orderId);
        setShowConfirm(true);
    };

    const confirmCancel = async () => {
        if (!orderToCancel) return;
        setCancellingId(orderToCancel);

        try {
            await axios.post(`http://localhost:8000/trading/${orderToCancel}/cancel`);
            await fetchOrders();
        } catch (err) {
            console.error("Lỗi hủy lệnh:", err);
            alert(err.response?.data?.detail || "Không thể hủy lệnh.");
        } finally {
            setCancellingId(null);
            setShowConfirm(false);
            setOrderToCancel(null);
        }
    };

    const removeOrder = (orderId) => {
        setOrders(prev => prev.filter(order => order.order_id !== orderId));
    };

    const isCancellable = (status) => {
        return ["PENDING", "PARTIALLY_FILLED"].includes(status?.toUpperCase());
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 500);
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
                        <th>Thao tác</th>
                        <th></th>
                    </tr>
                </thead>

                <tbody>
                    {orders.length === 0 ? (
                        <tr>
                            <td colSpan="8" className="empty-text">
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
                                            onClick={() => openConfirmCancel(order.order_id)}
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

            {/* Overlay Confirm Cancel */}
            {showConfirm && (
                <div className="overlay">
                    <div className="confirm-box">
                        <h3>Bạn có chắc muốn hủy lệnh?</h3>
                        <p>Mã lệnh: {orderToCancel}</p>

                        <div className="confirm-actions">
                            <button className="confirm-yes" onClick={confirmCancel}>
                                Hủy lệnh
                            </button>

                            <button className="confirm-no" onClick={() => setShowConfirm(false)}>
                                Thoát
                            </button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};

export default OrderHistory;