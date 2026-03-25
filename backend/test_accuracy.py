from app.database import SessionLocal
from app.services.analytics_service import get_menu_engineering_classification

def verify_accuracy():
    db = SessionLocal()
    try:
        results = get_menu_engineering_classification(db)
    finally:
        db.close()

    if not results:
        print("DATABASE IS EMPTY. No items mapped.")
        return

    print(f"Total Unique Items Configured: {len(results)}")
    
    total_qty = sum(item["total_quantity"] for item in results)
    total_prof = sum(item["profit"] for item in results)
    
    avg_qty = total_qty / len(results)
    avg_prof = total_prof / len(results)
    
    print(f"\n--- DETERMINISTIC THRESHOLDS ---")
    print(f"Average Popularity Target (Qty) : >= {avg_qty:.2f}")
    print(f"Average Profit Target     (Rev) : >= ${avg_prof:.2f}")
    print("--------------------------------\n")
    
    print(f"{'ITEM NAME':<30} | {'QTY':<5} | {'UNIT REV':<8} | {'TEST EXPECTED':<13} | {'ALGORITHM MAP':<13}")
    print("-" * 80)
    
    for item in results:
        qty = item["total_quantity"]
        prof = item["profit"]
        
        is_high_pop = qty >= avg_qty
        is_high_prof = prof >= avg_prof
        
        if is_high_pop and is_high_prof:
            expected = "Star"
        elif is_high_pop and not is_high_prof:
            expected = "Plowhorse"
        elif not is_high_pop and is_high_prof:
            expected = "Puzzle"
        else:
            expected = "Dog"
            
        name = item["item_name"][:29]
        actual = item["category"]
        
        flag = "✅" if expected == actual else "❌"
        print(f"{name:<30} | {qty:<5} | ${prof:<7.2f} | {expected:<13} | {actual:<13} {flag}")

if __name__ == "__main__":
    verify_accuracy()
