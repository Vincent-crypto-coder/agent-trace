"""
Quick Start — trace an agent with tool calls.
"""

from agent_trace import Tracer

tracer = Tracer(project="quickstart")


# Simulate a tool
def search_flights(date: str):
    with tracer.span("search_flights", kind="tool") as span:
        span.tool_name = "search_flights"
        span.tool_args = {"date": date}
        # Simulate work
        result = [{"flight": "CA123", "price": 1200}, {"flight": "MU456", "price": 980}]
        span.tool_result = result
        return result


def book_flight(flight: str):
    with tracer.span("book_flight", kind="tool") as span:
        span.tool_name = "book_flight"
        span.tool_args = {"flight": flight}
        result = {"status": "success", "booking_id": "ABC123"}
        span.tool_result = result
        return result


def agent(input: str):
    with tracer.span("plan", kind="llm") as span:
        span.model = "gpt-4o-mini"
        span.input_text = input
        span.output_text = "I will search for flights and book the cheapest one."
        span.prompt_tokens = 50
        span.completion_tokens = 20

    flights = search_flights("2026-06-11")

    with tracer.span("decide", kind="llm") as span:
        span.model = "gpt-4o-mini"
        span.input_text = f"Choose cheapest from: {flights}"
        span.output_text = "MU456 is cheapest at 980"
        span.prompt_tokens = 80
        span.completion_tokens = 15

    booking = book_flight("MU456")
    return booking


# Run it
result = tracer.run(agent, input="Book me the cheapest flight tomorrow")
print(f"Result: {result}")

# Print summary
tracer.summary()
