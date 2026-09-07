from fastapi import APIRouter
from transitiq_v2.api.models import UserInputs
from transitiq_v2.database.db import conn, create_issues_table
router = APIRouter()
cur = conn.cursor()


@router.post("/" , response_model=UserInputs)
async def post_issue(input_data : UserInputs):
    cur = conn.cursor()
    try:
        create_issues_table()
    except Exception as e:
        return {"error": str(e)}
    cur.execute("""
        INSERT INTO issues (origin, destination, carrier, issue_description)
        VALUES (%s, %s, %s, %s) RETURNING shipment_id
    """, (input_data.origin, input_data.destination, input_data.carrier, input_data.issue_description))
    shipment_id = cur.fetchone()[0]
    cur.close()
    conn.commit()
    return {"shipment_id": shipment_id , "origin": input_data.origin, "destination": input_data.destination, "carrier": input_data.carrier, "issue_description": input_data.issue_description}

@router.get("/get_all_issues")
async def get_issue():
    cur = conn.cursor()
    cur.execute("SELECT * FROM issues")
    issues = cur.fetchall()
    cur.close()
    return issues

@router.get("/get_issue/{shipment_id}")
async def get_issue_by_id(shipment_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM issues WHERE shipment_id = %s", (shipment_id,))
    issue = cur.fetchone()
    cur.close()
    return issue
