import json
from dataclasses import dataclass
from typing import Dict, List

from llm import generate_json, generate_text


@dataclass
class Customer:
    name: str
    email: str
    company: str
    industry: str
    lead_score: int
    last_contact_days_ago: int
    annual_revenue: int
    current_tool: str
    region: str

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "Customer":
        return cls(
            name=row["name"],
            email=row["email"],
            company=row["company"],
            industry=row["industry"],
            lead_score=int(row["lead_score"]),
            last_contact_days_ago=int(row["last_contact_days_ago"]),
            annual_revenue=int(row["annual_revenue"]),
            current_tool=row["current_tool"],
            region=row["region"],
        )


class EmailWriterAgent:
    """
    A simple "agent" with its own style and goal, implemented via a
    distinct system prompt.
    """

    def __init__(self, name: str, style_description: str) -> None:
        self.name = name
        self.style_description = style_description

    def draft_email(self, customer: Customer, product_name: str, product_value_prop: str) -> str:
        system_prompt = (
            "You are an expert B2B sales email writer. "
            f"Your specific style: {self.style_description}. "
            "Write a concise outbound sales email.\n"
            "- 3 short paragraphs max\n"
            "- Clear subject line\n"
            "- Personalized using the customer profile\n"
            "- One clear call to action (15–30 minute call)\n"
            "- Neutral, professional tone\n"
        )

        user_prompt = f"""
Customer profile:
- Name: {customer.name}
- Company: {customer.company}
- Industry: {customer.industry}
- Region: {customer.region}
- Lead score: {customer.lead_score}
- Last contact (days ago): {customer.last_contact_days_ago}
- Annual revenue: {customer.annual_revenue}
- Current tool: {customer.current_tool}

Product:
- Name: {product_name}
- Value proposition: {product_value_prop}

Write the full email including subject line.
"""
        prompt = f"{system_prompt}\n\n{user_prompt}"
        return generate_text(prompt, temperature=0.8)


class SalesManagerAgent:
    """
    Manager agent that:
    - selects which leads to contact
    - chooses the best email among drafts from writer agents
    """

    def __init__(self) -> None:
        ...

    def select_leads(self, customers: List[Customer]) -> List[Customer]:
        """
        Very simple lead selection heuristic:
        - lead_score >= 80
        - last_contact_days_ago >= 14
        """
        selected = [
            c
            for c in customers
            if c.lead_score >= 80 and c.last_contact_days_ago >= 14
        ]
        return selected

    def choose_best_email(self, customer: Customer, drafts: Dict[str, str]) -> Dict[str, str]:
        """
        Ask the LLM (as a manager) to evaluate and pick the best email draft.
        Returns a dict with keys:
        - chosen_agent
        - final_email (optionally lightly edited by the manager)
        - reasoning
        """
        system_prompt = (
            "You are a sales manager evaluating 3 outbound sales emails "
            "for a single B2B prospect. You must pick the single best email "
            "and can lightly edit it for clarity and impact. "
            "Return ONLY a JSON object with keys: chosen_agent, final_email, reasoning."
        )

        drafts_text = "\n\n".join(
            f"Agent: {agent_name}\n---\n{email}\n---"
            for agent_name, email in drafts.items()
        )

        user_prompt = f"""
Customer profile:
- Name: {customer.name}
- Company: {customer.company}
- Industry: {customer.industry}
- Region: {customer.region}
- Lead score: {customer.lead_score}
- Last contact (days ago): {customer.last_contact_days_ago}
- Annual revenue: {customer.annual_revenue}
- Current tool: {customer.current_tool}

Here are 3 candidate outbound emails from different agents:

{drafts_text}

Evaluate them on:
- Personalization and relevance
- Clarity of value proposition
- Strength but politeness of the CTA

Pick the single best email. You MAY make small edits to improve it, but keep the original tone.
"""
        prompt = f"{system_prompt}\n\n{user_prompt}"

        data = generate_json(prompt, temperature=0.4)

        # If Gemini didn't return valid JSON, fall back to concatenated drafts
        if "_raw" in data:
            raw = data["_raw"]
            return {
                "chosen_agent": "unknown",
                "final_email": "\n".join(drafts.values()),
                "reasoning": f"Model returned non-JSON content: {raw}",
            }

        # Basic validation / defaults
        chosen_agent = data.get("chosen_agent") or "unknown"
        final_email = data.get("final_email") or drafts.get(chosen_agent) or "\n".join(drafts.values())
        reasoning = data.get("reasoning") or ""

        return {
            "chosen_agent": chosen_agent,
            "final_email": final_email.strip(),
            "reasoning": reasoning.strip(),
        }

