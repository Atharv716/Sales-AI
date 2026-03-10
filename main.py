import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from agents import Customer, EmailWriterAgent, SalesManagerAgent
from email_sender import send_email


BASE_DIR = Path(__file__).parent


def load_customers() -> list[Customer]:
    data_path = BASE_DIR / "data" / "customers.csv"
    customers: list[Customer] = []
    with data_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            customers.append(Customer.from_row(row))
    return customers


def build_agents() -> tuple[list[EmailWriterAgent], SalesManagerAgent]:
    writer_agents = [
        EmailWriterAgent(
            name="value_focus",
            style_description="laser-focused on quantifying business value, ROI, and hard numbers while staying concise.",
        ),
        EmailWriterAgent(
            name="relationship_focus",
            style_description="warm, consultative tone, emphasizes partnership, trust, and understanding the customer's context.",
        ),
        EmailWriterAgent(
            name="urgency_focus",
            style_description="direct and to-the-point with a gentle sense of urgency, highlighting time-sensitive benefits.",
        ),
    ]
    manager = SalesManagerAgent()
    return writer_agents, manager


def main() -> None:
    load_dotenv()

    product_name = os.getenv("PRODUCT_NAME", "SalesAI Copilot")
    product_value_prop = os.getenv(
        "PRODUCT_VALUE_PROP",
        "helps sales teams automatically prioritize leads and draft highly personalized outreach, saving hours per week.",
    )

    customers = load_customers()
    writer_agents, manager = build_agents()

    selected_customers = manager.select_leads(customers)
    if not selected_customers:
        print("No customers selected by SalesManager heuristics.")
        return

    print(f"SalesManager selected {len(selected_customers)} customer(s) for outreach.\n")

    for customer in selected_customers:
        print(f"=== Working on customer: {customer.name} ({customer.company}) ===")

        # 1) Each writer agent drafts an email
        drafts: dict[str, str] = {}
        for agent in writer_agents:
            drafts[agent.name] = agent.draft_email(
                customer=customer,
                product_name=product_name,
                product_value_prop=product_value_prop,
            )

        # 2) Manager chooses the best email
        decision = manager.choose_best_email(customer, drafts)
        chosen_agent = decision["chosen_agent"]
        final_email = decision["final_email"]
        reasoning = decision.get("reasoning", "")

        print(f"Manager chose agent: {chosen_agent}")
        if reasoning:
            print(f"Reasoning: {reasoning}\n")

        # 3) Send email (or print in DRY_RUN mode)
        send_email(to_address=customer.email, email_text=final_email)


if __name__ == "__main__":
    main()

