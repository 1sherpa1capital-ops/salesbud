from salesbud.database import get_db

def reset_dm_step(lead_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET sequence_step = 0, last_dm_sent_at = NULL WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    print(f"Lead {lead_id} dm step reset to 0")

reset_dm_step(1)
