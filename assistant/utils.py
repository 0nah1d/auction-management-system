from datetime import datetime, timezone
import math


def dynamic_bid_logic(current_bid, max_bid, auction_end_time):
    time_remaining = (auction_end_time - datetime.now(timezone.utc)).total_seconds()
    bid_gap = max_bid - current_bid

    if bid_gap <= 0:
        return None

    auction_duration = (auction_end_time - datetime.now(timezone.utc)).total_seconds()
    final_stage_time = auction_duration * 0.1

    if time_remaining > final_stage_time * 5:
        increment = max(1, math.ceil(bid_gap * 0.01))
    elif final_stage_time < time_remaining <= final_stage_time * 5:
        increment = max(5, math.ceil(bid_gap * 0.02))
    else:
        increment = max(10, math.ceil(bid_gap * 0.05))

    return min(current_bid + increment, max_bid)
