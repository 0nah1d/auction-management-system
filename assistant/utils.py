from datetime import datetime, timezone, timedelta
import math


def dynamic_bid_logic(current_bid, max_bid, auction_end_time):
    time_remaining = (auction_end_time - datetime.now(timezone.utc)).total_seconds()
    bid_gap = max_bid - current_bid

    if bid_gap <= 0:
        return None

    # Define the final stage as 10% of the time remaining
    final_stage_time = time_remaining * 0.1

    if time_remaining > final_stage_time * 5:
        increment = max(1, math.ceil(bid_gap * 0.01))
    elif final_stage_time < time_remaining <= final_stage_time * 5:
        increment = max(5, math.ceil(bid_gap * 0.02))
    else:
        increment = max(10, math.ceil(bid_gap * 0.05))

    return min(current_bid + increment, max_bid)


# Example Usage for understanding
if __name__ == "__main__":
    current_bid_amount = 100
    max_bid_amount = 500
    auction_end_time_ = datetime.now(timezone.utc) + timedelta(minutes=30)

    new_bid = dynamic_bid_logic(current_bid_amount, max_bid_amount, auction_end_time_)

    print(f"Current Bid: {current_bid_amount}")
    print(f"Max Bid: {max_bid_amount}")
    print(f"Auction End Time (UTC): {auction_end_time_}")
    print(f"Time Remaining (seconds): {(auction_end_time_ - datetime.now(timezone.utc)).total_seconds()}")
    print(f"New Bid: {new_bid}")
