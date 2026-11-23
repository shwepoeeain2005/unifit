"""Fix known wrong university_card addresses, then re-export."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "maintenance" / "unifit.sqlite"

FIXES = {
    83: "📍 Monywa, Sagaing Region, Myanmar",
    155: "📍 Hlegu, Yangon Region, Myanmar",
}


def main() -> None:
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        for card_id, address in FIXES.items():
            before = conn.execute(
                "SELECT id, name, address FROM university_card WHERE id = ?",
                (card_id,),
            ).fetchone()
            if before is None:
                raise SystemExit(f"Missing university_card id={card_id}")
            conn.execute(
                "UPDATE university_card SET address = ? WHERE id = ?",
                (address, card_id),
            )
            after = conn.execute(
                "SELECT id, name, address FROM university_card WHERE id = ?",
                (card_id,),
            ).fetchone()
            print(f"id={card_id} {after['name']}")
            print(f"  before: {before['address']}")
            print(f"  after:  {after['address']}")
        conn.commit()
    print("card address fixes committed")


if __name__ == "__main__":
    main()
