from pyflink.common import Types

order_raw_type_info = Types.ROW_NAMED(
    [
        "order_id", "user_id", "stock_symbol", "order_type", 
        "price", "quantity", "created_timestamp", "action_type"
    ],
    [
        Types.STRING(), Types.STRING(), Types.STRING(), Types.STRING(),
        Types.DOUBLE(), Types.INT(), Types.STRING(), Types.STRING(),
    ]
)


pending_order_type_info = Types.ROW_NAMED(
    [
        "order_id",
        "user_id",
        "stock_symbol",
        "order_type",
        "price",
        "quantity",           
        "created_timestamp",
        "action_type",
        "status",             
        "total_filled_quantity", 
        "total_filled_value"  
    ],
    [
        Types.STRING(),        
        Types.STRING(),      
        Types.STRING(),        
        Types.STRING(),        
        Types.DOUBLE(),        
        Types.INT(),           
        Types.SQL_TIMESTAMP(), 
        Types.STRING(),        
        Types.STRING(),        
        Types.INT(),          
        Types.DOUBLE()         
    ]
)


matched_type_info = Types.ROW_NAMED(
    [
        "trade_id",
        "stock_symbol",
        "buy_order_id",
        "sell_order_id",
        "buy_user_id",
        "sell_user_id",
        "matched_price",
        "matched_quantity",
        "trade_timestamp"
    ],
    [
        Types.STRING(), Types.STRING(), Types.STRING(),
        Types.STRING(), Types.STRING(), Types.STRING(),
        Types.DOUBLE(), Types.INT(), Types.SQL_TIMESTAMP()
    ]
)


order_history_type_info = Types.ROW_NAMED(
    [
        "order_id",
        "status_at_event",
        "filled_quantity_at_event",
        "filled_price_avg_at_event",
        "event_timestamp",
        "event_details"
    ],
    [
        Types.STRING(), Types.STRING(), Types.INT(),
        Types.DOUBLE(), Types.SQL_TIMESTAMP(), Types.STRING()
    ]
)