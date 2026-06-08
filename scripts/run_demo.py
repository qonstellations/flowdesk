"""Demo flow simulation script for FlowDesk.

Simulates student complaints flowing through the full LangGraph
workflow to demonstrate classification, routing, and SLA assignment.
"""

from __future__ import annotations

from backend import db, workflow


# ── Simulation helpers ─────────────────────────────────────────────────


def simulate_complaint(message: str, telegram_id: str = "1001") -> dict:
    """Simulate a student complaint through the workflow.

    Args:
        message: The raw complaint text from a student.
        telegram_id: Telegram ID of the student filing the complaint.

    Returns:
        A dict containing the workflow result (ticket, classification, etc.).
    """
    return workflow.run_workflow(raw_message=message, telegram_id=telegram_id)


# ── Demo flow ──────────────────────────────────────────────────────────


def run_demo_flow() -> None:
    """Run a full demo sequence with multiple complaints."""
    complaints = [
        {
            "message": (
                "The Wi-Fi in Block C has been down since morning, "
                "cannot attend online classes"
            ),
            "telegram_id": "1001",
        },
        {
            "message": (
                "There is a major water pipe burst in the 3rd floor "
                "corridor of hostel block B"
            ),
            "telegram_id": "1002",
        },
        {
            "message": (
                "The food in the south mess has been terrible, "
                "found insects in the dal today"
            ),
            "telegram_id": "1003",
        },
    ]

    for i, complaint in enumerate(complaints, start=1):
        print(f"\n{'─' * 50}")
        print(f"📨 Complaint {i}/{len(complaints)}")
        print(f"   From: telegram_id={complaint['telegram_id']}")
        print(f"   Message: {complaint['message']}")
        print(f"{'─' * 50}")

        result = simulate_complaint(
            message=complaint["message"],
            telegram_id=complaint["telegram_id"],
        )

        print(f"   🎫 Ticket ID   : {result.get('ticket_id')}")
        print(f"   📝 Title       : {result.get('title')}")
        print(f"   📂 Category    : {result.get('category')}")
        print(f"   ⚡ Priority    : {result.get('priority')}")
        print(f"   🏢 Department  : {result.get('assigned_dept')}")
        print(f"   ⏰ SLA Deadline: {result.get('sla_deadline')}")
        print(f"   📌 Status      : {result.get('status')}")
        print(f"   📍 Location    : {result.get('location')}")

        notes = result.get("agent_notes", [])
        if notes:
            print("   📋 Agent Notes :")
            for note in notes:
                print(f"      • {note}")


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the demo."""
    print("=" * 60)
    print("FlowDesk — Demo Flow Simulation")
    print("=" * 60)

    print("\n🔧 Initialising database …")
    db.init_db()
    print("  ✅ Database initialised")

    print("\n🚀 Running demo complaints through the workflow …")
    run_demo_flow()

    print("\n" + "=" * 60)
    print("✅ Demo flow complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
