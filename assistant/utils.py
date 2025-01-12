from datetime import datetime, timezone
import math


def dynamic_bid_logic(current_bid, max_bid, auction_end_time):
    current_time = datetime.now(timezone.utc)
    time_remaining = (auction_end_time - current_time).total_seconds()

    bid_gap = max_bid - current_bid
    if bid_gap <= 0:
        return None  # No further bids can be placed

    # Calculate dynamic time thresholds
    auction_duration = (auction_end_time - current_time).total_seconds()
    final_stage_time = math.ceil(auction_duration * 0.1)  # Final stage is last 10% of the auction

    # Determine increment dynamically based on stage
    if time_remaining > final_stage_time * 5:  # Early stage (50% of auction time)
        increment = max(1, math.ceil(bid_gap * 0.01))  # 1% of bid gap
    elif final_stage_time * 5 >= time_remaining > final_stage_time:  # Mid-stage (10%-50%)
        increment = max(5, math.ceil(bid_gap * 0.02))  # 2% of bid gap
    else:  # Final stage (last 10% of auction time)
        increment = max(10, math.ceil(bid_gap * 0.05))  # 5% of bid gap

    next_bid = current_bid + increment

    # Ensure next bid doesn't exceed max bid
    return min(next_bid, max_bid)
