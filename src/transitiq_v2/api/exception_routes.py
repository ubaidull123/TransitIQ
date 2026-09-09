from fastapi import APIRouter
from transitiq_v2.api.models import UserInputs
from transitiq_v2.database.db import conn, create_issues_table
router = APIRouter()


@router.post("/exceptions" , response_model=UserInputs)
async def post_issue(input_data : UserInputs):
    try:
        create_issues_table()
    except Exception as e:
        return {"error": str(e)}

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO issues (origin, destination, carrier, issue_description)
            VALUES (%s, %s, %s, %s) RETURNING shipment_id
        """, (input_data.origin, input_data.destination, input_data.carrier, input_data.issue_description))
        shipment_id = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    return {"shipment_id": shipment_id , "origin": input_data.origin, "destination": input_data.destination, "carrier": input_data.carrier, "issue_description": input_data.issue_description}

@router.get("/exceptions")
async def get_issue():
    cur = conn.cursor()
    cur.execute("SELECT * FROM issues")
    issues = cur.fetchall()
    cur.close()
    return issues

@router.get("/exceptions/{id}")
async def get_issue_by_id(id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM issues WHERE shipment_id = %s", (id,))
    issue = cur.fetchone()
    cur.close()
    return issue

@router.patch("/exceptions/{id}")
def update_issue(id: int, data: dict):
    cur = conn.cursor()
    cur.execute("UPDATE issues SET issue_description = %s WHERE shipment_id = %s", (data["issue_description"], id))
    conn.commit()
    cur.close()
    return {"message": "Issue updated successfully"}


@router.patch("/exceptions/{id}/status")
def update_issue_status(id: int, status: str):
    cur = conn.cursor()
    cur.execute("UPDATE issues SET status = %s WHERE shipment_id = %s", (status, id))
    conn.commit()
    cur.close()
    return {"message": "Issue status updated successfully"}
