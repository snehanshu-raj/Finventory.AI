"""Price insight aggregation job."""

import asyncio
import logging
from datetime import datetime

from app.config import settings
from app.repositories.inventory_repository import inventory_repo
from app.repositories.price_repository import price_repo

logger = logging.getLogger(__name__)


async def _aggregate_insights() -> int:
    """Aggregate price observations into price insights for all users/items."""
    # Get all unique user IDs from inventory
    all_states = await inventory_repo.find_all_states_global()

    # Collect unique user IDs
    user_ids = list({s["userId"] for s in all_states})
    count = 0

    for user_id in user_ids:
        agg_data = await price_repo.aggregate_all_items_by_store(user_id, window_days=30)

        # Group by item
        items: dict[str, list] = {}
        for row in agg_data:
            item_id = row["_id"]["item"]
            item_name = row["_id"]["itemName"]
            store = row["_id"]["store"]
            key = item_id
            if key not in items:
                items[key] = {"name": item_name, "stores": []}
            items[key]["stores"].append({
                "storeName": store or "Unknown",
                "avgUnitPrice": round(row["avgUnitPrice"], 4),
                "samples": row["samples"],
                "lastSeen": row.get("lastSeen"),
            })

        for item_id, data in items.items():
            stores = data["stores"]
            # Find best store with minimum samples
            best = None
            confidence = None
            for s in sorted(stores, key=lambda x: x["avgUnitPrice"]):
                if s["samples"] >= settings.min_price_samples:
                    total = sum(x["samples"] for x in stores)
                    best = s["storeName"]
                    confidence = round(s["samples"] / total, 2) if total else None
                    break

            await price_repo.upsert_insight(user_id, item_id, "30d", {
                "userId": user_id,
                "canonicalItemId": item_id,
                "canonicalName": data["name"],
                "window": "30d",
                "generatedAt": datetime.utcnow(),
                "stores": stores,
                "bestStore": best,
                "confidence": confidence,
                "insight": f"Best store for {data['name']} is {best}" if best else "Not enough data",
            })
            count += 1

    return count


def run_price_aggregation() -> None:
    """Entry point called by APScheduler."""
    logger.info("Starting price insight aggregation job...")
    loop = asyncio.new_event_loop()
    try:
        count = loop.run_until_complete(_aggregate_insights())
        logger.info("Price aggregation job completed. Updated %d insights.", count)
    except Exception as e:
        logger.exception("Price aggregation job failed: %s", e)
    finally:
        loop.close()
