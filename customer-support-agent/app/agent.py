# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from google.adk.agents import Agent, Context
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import node, Workflow, Edge, START
# GCP authentication is skipped for API key use.




@node
def classifier(ctx: Context, node_input: str):
    """Classifies if the query is related to shipping or not."""
    q = node_input.lower()
    shipping_keywords = ["rate", "track", "deliver", "return", "ship", "cost", "price", "package", "box", "mail"]
    if any(k in q for k in shipping_keywords):
        ctx.route = "shipping"
    else:
        ctx.route = "unrelated"
    return node_input


shipping_faq_agent = Agent(
    name="shipping_faq_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a customer support representative for a shipping company. 
Answer user queries related to shipping rates, tracking, delivery, and returns accurately and concisely.""",
)


@node
def polite_decline(ctx: Context, node_input: str):
    """Politely declines non-shipping queries."""
    return "I apologize, but I can only assist with shipping-related inquiries such as rates, tracking, delivery, and returns. How can I help you with your shipping needs today?"


workflow = Workflow(
    name="customer_support_workflow",
    edges=[
        Edge(from_node=START, to_node=classifier),
        Edge(from_node=classifier, to_node=shipping_faq_agent, route="shipping"),
        Edge(from_node=classifier, to_node=polite_decline, route="unrelated"),
    ]
)


app = App(
    root_agent=workflow,
    name="customer-support-agent",
)
