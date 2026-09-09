import json

from fastapi import APIRouter, HTTPException

from transitiq_v2.api.models import AnalysisResponse
from transitiq_v2.database.db import (
    conn,
    create_analysis_runs_table,
    create_issues_table,
)
from transitiq_v2.llm.openrouter_service import OPENROUTER_MODEL
from transitiq_v2.workflow.agent import agent


router = APIRouter()


def _analysis_from_row(row) -> dict:
    return {
        "id": row[0],
        "exception_id": row[1],
        "exception_type": row[2],
        "severity": row[3],
        "missing_information": row[4],
        "recommended_actions": json.loads(row[5]),
        "model_name": row[6],
        "created_at": row[7],
    }


def _load_exception(exception_id: int):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT shipment_id, origin, destination, carrier, issue_description
            FROM issues
            WHERE shipment_id = %s
            """,
            (exception_id,),
        )
        issue = cur.fetchone()
    finally:
        cur.close()

    if issue is None:
        raise HTTPException(status_code=404, detail="Exception not found")

    return issue


@router.post("/exceptions/{exception_id}/analyze", response_model=AnalysisResponse)
def analyze_exception(exception_id: int):
    create_issues_table()
    issue = _load_exception(exception_id)
    description = issue[4].strip()

    if len(description) < 10 or len(description.split()) < 2:
        raise HTTPException(
            status_code=422,
            detail="Issue description is too short or unclear",
        )

    initial_state = {
        "issue_id": issue[0],
        "origin": issue[1],
        "destination": issue[2],
        "carrier": issue[3],
        "description": description,
        "current_step": "classification",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Analyze shipment {issue[0]}. "
                    f"Origin: {issue[1]}. "
                    f"Destination: {issue[2]}. "
                    f"Carrier: {issue[3]}. "
                    f"Problem: {description}"
                ),
            }
        ],
    }

    try:
        result = agent.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Agent analysis failed") from exc

    exception_type = result.get("exception_type")
    severity = result.get("severity")
    missing_information = result.get("missing_info")
    recommended_actions = result.get("recommendations")

    if (
        not exception_type
        or not severity
        or missing_information is None
        or not isinstance(recommended_actions, list)
    ):
        raise HTTPException(
            status_code=502,
            detail="Agent returned an incomplete analysis",
        )

    create_analysis_runs_table()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO analysis_runs (
                exception_id,
                exception_type,
                severity,
                missing_information,
                recommended_actions,
                model_name
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                exception_id,
                exception_type,
                severity,
                missing_information,
                recommended_actions,
                model_name,
                created_at
            """,
            (
                exception_id,
                exception_type,
                severity,
                missing_information,
                json.dumps(recommended_actions),
                OPENROUTER_MODEL,
            ),
        )
        analysis = cur.fetchone()
        cur.execute(
            """
            UPDATE issues
            SET status = 'analyzed', updated_at = CURRENT_TIMESTAMP
            WHERE shipment_id = %s
            """,
            (exception_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    return _analysis_from_row(analysis)


@router.get("/exceptions/{exception_id}/analyses", response_model=list[AnalysisResponse],)
def get_analysis_history(exception_id: int):
    create_analysis_runs_table()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                id,
                exception_id,
                exception_type,
                severity,
                missing_information,
                recommended_actions,
                model_name,
                created_at
            FROM analysis_runs
            WHERE exception_id = %s
            ORDER BY created_at, id
            """,
            (exception_id,),
        )
        analyses = cur.fetchall()
    finally:
        cur.close()

    return [_analysis_from_row(analysis) for analysis in analyses]


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int):
    create_analysis_runs_table()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                id,
                exception_id,
                exception_type,
                severity,
                missing_information,
                recommended_actions,
                model_name,
                created_at
            FROM analysis_runs
            WHERE id = %s
            """,
            (analysis_id,),
        )
        analysis = cur.fetchone()
    finally:
        cur.close()

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _analysis_from_row(analysis)
