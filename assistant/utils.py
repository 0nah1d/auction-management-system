from datetime import datetime, timezone, timedelta
import math


def dynamic_bid_logic(current_bid, max_bid, auction_end_time, auction_created_at):
    # Calculate the total auction duration and time remaining
    total_auction_duration = (auction_end_time - auction_created_at).total_seconds()
    time_remaining = (auction_end_time - datetime.now(timezone.utc)).total_seconds()
    bid_gap = max_bid - current_bid

    if bid_gap <= 0 or time_remaining <= 0 or total_auction_duration <= 0:
        return None

    # Calculate the auction's progress as a percentage
    auction_progress = (1 - (time_remaining / total_auction_duration)) * 100

    # Dynamic increment logic based on auction progress
    if auction_progress < 50:
        # Early stage: Small increments
        increment = max(1, math.ceil(bid_gap * 0.01))
    elif 50 <= auction_progress < 80:
        # Mid stage: Moderate increments
        increment = max(5, math.ceil(bid_gap * 0.02))
    else:
        # Final stage: Aggressive increments
        increment = max(10, math.ceil(bid_gap * 0.05))

    # Ensure the next bid does not exceed max_bid
    next_bid = current_bid + increment
    return min(next_bid, max_bid)


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
