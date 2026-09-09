from transitiq_v2.api.exception_routes import get_issue, get_issue_by_id
import asyncio

async def get_graph_input(shipment_id: int):
    """
    Retrieves the issue details for a given shipment_id and returns them as a dictionary.
    """
    issue = await get_issue_by_id(shipment_id)
    if issue:
        return {
            "issue_id": issue[0],
            "origin": issue[1], 
            "destination": issue[2],
            "carrier": issue[3],
            "description": issue[4]
        }
    else:
        return None


def get_all_shipment_ids():
    """
    Retrieves all shipment IDs from the database.
    """
    issues = asyncio.run(get_issue())
    return [issue[0] for issue in issues]


def serve_issues():
    """
    Generator function to yield issues one by one for processing.
    """
    shipment_ids = get_all_shipment_ids()
    for shipment_id in shipment_ids:
        issue_details = asyncio.run(get_graph_input(shipment_id))
        if issue_details:
            yield issue_details
            

    return None

if __name__ == "__main__":
    print("Serving issues:")
    for issue in serve_issues():
        print(issue)
