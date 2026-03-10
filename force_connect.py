from salesbud.database import get_db

def set_connected(lead_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = 'connected' WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    print(f"Lead {lead_id} marked as connected")

set_connected(1)
