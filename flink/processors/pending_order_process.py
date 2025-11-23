import uuid
from datetime import datetime
from pyflink.datastream import KeyedProcessFunction, RuntimeContext, OutputTag
from pyflink.datastream.state import ListStateDescriptor
from common.schemas import pending_order_type_info, matched_type_info, order_history_type_info
import logging
from pyflink.common import Row

logger = logging.getLogger(__name__)

order_update_tag = OutputTag("order_updates", order_history_type_info)


class PendingOrderProcessFunction(KeyedProcessFunction):

    def open(self, runtime_context: RuntimeContext):
        self.buy_order_state = runtime_context.get_list_state(
            ListStateDescriptor("buy_order_state", pending_order_type_info)
        )
        self.sell_order_state = runtime_context.get_list_state(
            ListStateDescriptor("sell_order_state", pending_order_type_info)
        )
        logger.info("State descriptors initialized.")

    def _create_history_event(self, order, status, details):
        avg_price = (order.total_filled_value / order.total_filled_quantity) if order.total_filled_quantity > 0 else 0.0
        return Row(
            order_id=str(order.order_id),
            status_at_event=status,
            filled_quantity_at_event=int(order.total_filled_quantity),
            filled_price_avg_at_event=float(avg_price),
            event_timestamp=datetime.now(),
            event_details=details
        )

    def _match_order(self, order_to_match, ctx: RuntimeContext):
        order_type = order_to_match.order_type.upper()
        own_state = self.buy_order_state if order_type == "BUY" else self.sell_order_state
        opposite_state = self.sell_order_state if order_type == "BUY" else self.buy_order_state

        # Lấy danh sách lệnh đối phương, sort theo giá
        opposite_orders = sorted(
            list(opposite_state.get()), 
            key=lambda o: o.price, 
            reverse=(order_type == "SELL")
        )
        remaining_quantity = order_to_match.quantity
        remaining_opposite_orders = []

        for opp_order in opposite_orders:
            if remaining_quantity <= 0:
                remaining_opposite_orders.append(opp_order)
                continue

            # Kiểm tra match
            is_match = (order_type == "BUY" and order_to_match.price >= opp_order.price) or \
                    (order_type == "SELL" and order_to_match.price <= opp_order.price)

            if is_match:
                matched_qty = min(remaining_quantity, opp_order.quantity)
                match_price = opp_order.price

                # Cập nhật lệnh đối phương
                opp_order_data = opp_order.as_dict()
                opp_order_data['total_filled_quantity'] += matched_qty
                opp_order_data['total_filled_value'] += matched_qty * match_price
                status_opp = 'FILLED' if opp_order_data['quantity'] == opp_order_data['total_filled_quantity'] else 'PARTIALLY_FILLED'
                yield (order_update_tag, self._create_history_event(Row(**opp_order_data), status_opp,
                    f"Matched {matched_qty} shares with {order_to_match.order_id}"))

                # Cập nhật lệnh mới (order_to_match)
                order_to_match_data = order_to_match.as_dict()
                order_to_match_data['total_filled_quantity'] += matched_qty
                order_to_match_data['total_filled_value'] += matched_qty * match_price
                status_own = 'FILLED' if remaining_quantity - matched_qty == 0 else 'PARTIALLY_FILLED'
                yield (order_update_tag, self._create_history_event(Row(**order_to_match_data), status_own,
                    f"Matched {matched_qty} shares with {opp_order.order_id}"))

                # Tạo trade record
                buy_order = order_to_match if order_type == "BUY" else opp_order
                sell_order = opp_order if order_type == "BUY" else order_to_match
                yield Row(
                    trade_id=str(uuid.uuid4()),
                    stock_symbol=buy_order.stock_symbol,
                    buy_order_id=str(buy_order.order_id),
                    sell_order_id=str(sell_order.order_id),
                    buy_user_id=str(buy_order.user_id),
                    sell_user_id=str(sell_order.user_id),
                    matched_price=float(match_price),
                    matched_quantity=int(matched_qty),
                    trade_timestamp=datetime.now()
                )

                # Cập nhật remaining
                remaining_quantity -= matched_qty
                if opp_order.quantity > matched_qty:
                    opp_order_data['quantity'] -= matched_qty
                    remaining_opposite_orders.append(Row(**opp_order_data))
            else:
                remaining_opposite_orders.append(opp_order)

        # Nếu còn quantity chưa khớp, lưu vào state
        if remaining_quantity > 0:
            order_to_match_data = order_to_match.as_dict()
            order_to_match_data['quantity'] = remaining_quantity
            own_state.add(Row(**order_to_match_data))

        # Cập nhật lại state đối phương
        opposite_state.update(remaining_opposite_orders)


    def process_element(self, value, ctx: RuntimeContext):
        action = value.action_type.upper()

        if action == "NEW":
            value_data = value.as_dict()
            value_data.update({'status': 'PENDING', 'total_filled_quantity': 0, 'total_filled_value': 0.0})
            order_with_state = Row(**value_data)
            

            yield (order_update_tag, self._create_history_event(order_with_state, 'PENDING', 'Order received'))
            
            for result in self._match_order(order_with_state, ctx):
                yield result

        elif action == "UPDATE" or action == "CANCEL":
            order_id_to_modify = value.order_id
            order_found, original_order = False, None
            for state in [self.buy_order_state, self.sell_order_state]:
                current_orders = list(state.get())
                remaining_orders = [o for o in current_orders if o.order_id != order_id_to_modify]
                if len(remaining_orders) < len(current_orders):
                    order_found = True
                    original_order = next(o for o in current_orders if o.order_id == order_id_to_modify)
                    state.update(remaining_orders)
                    break
            
            if order_found:
                if action == "UPDATE":
                    updated_data = original_order.as_dict()
                    updated_data.update({
                        'price': value.price if value.price is not None else original_order.price,
                        'quantity': value.quantity if value.quantity is not None else original_order.quantity
                    })
                    updated_order = Row(**updated_data)
                    

                    yield (order_update_tag, self._create_history_event(updated_order, 'PENDING', 'Order updated'))
                    for result in self._match_order(updated_order, ctx):
                        yield result
                else:

                    yield (order_update_tag, self._create_history_event(original_order, 'CANCELLED', 'Order cancelled'))
            else:
                logger.warning(f"Could not find order {order_id_to_modify} to {action}.")