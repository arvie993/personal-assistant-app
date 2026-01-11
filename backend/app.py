"""
Personal Assistant API Backend
==============================
FastAPI backend that exposes Semantic Kernel functionality with real APIs.
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Annotated, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel import Kernel
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, get_bearer_token_provider


# ============================================================================
# PLUGINS WITH REAL APIs
# ============================================================================

class WeatherPlugin:
    """Real weather data from wttr.in API."""
    
    @kernel_function(
        name="GetCurrentWeather",
        description="Get the current REAL weather for any city in the world."
    )
    def get_current_weather(
        self,
        city: Annotated[str, "The name of the city to get weather for"]
    ) -> str:
        try:
            url = f"https://wttr.in/{city}?format=j1"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            current = data["current_condition"][0]
            location = data["nearest_area"][0]
            
            temp_f = current["temp_F"]
            temp_c = current["temp_C"]
            feels_like_f = current["FeelsLikeF"]
            condition = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind_mph = current["windspeedMiles"]
            wind_dir = current["winddir16Point"]
            
            city_name = location["areaName"][0]["value"]
            country = location["country"][0]["value"]
            
            return (
                f"📍 {city_name}, {country}\n"
                f"🌡️ Temperature: {temp_f}°F ({temp_c}°C) | Feels like: {feels_like_f}°F\n"
                f"☁️ Condition: {condition}\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind_mph} mph {wind_dir}"
            )
        except Exception as e:
            return f"Could not fetch weather for {city}: {str(e)}"
    
    @kernel_function(
        name="GetWeatherForecast",
        description="Get a 3-day weather forecast for any city."
    )
    def get_weather_forecast(
        self,
        city: Annotated[str, "The name of the city to get forecast for"]
    ) -> str:
        try:
            url = f"https://wttr.in/{city}?format=j1"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            forecast_data = data["weather"]
            location = data["nearest_area"][0]
            city_name = location["areaName"][0]["value"]
            
            result = f"📅 3-Day Forecast for {city_name}:\n"
            
            for day in forecast_data[:3]:
                date = day["date"]
                max_temp = day["maxtempF"]
                min_temp = day["mintempF"]
                hourly = day["hourly"]
                midday = hourly[4] if len(hourly) > 4 else hourly[0]
                condition = midday["weatherDesc"][0]["value"]
                rain_chance = midday["chanceofrain"]
                
                result += f"\n📆 {date}: {min_temp}°F - {max_temp}°F | {condition} | 🌧️ {rain_chance}% rain"
            
            return result
        except Exception as e:
            return f"Could not fetch forecast for {city}: {str(e)}"


class CurrencyPlugin:
    """Real currency exchange rates from frankfurter.app."""
    
    @kernel_function(
        name="ConvertCurrency",
        description="Convert between currencies using REAL live exchange rates."
    )
    def convert_currency(
        self,
        amount: Annotated[float, "Amount to convert"],
        from_currency: Annotated[str, "Source currency code (e.g., USD, EUR, GBP, JPY)"],
        to_currency: Annotated[str, "Target currency code"]
    ) -> str:
        try:
            from_curr = from_currency.upper()
            to_curr = to_currency.upper()
            
            url = f"https://api.frankfurter.app/latest?amount={amount}&from={from_curr}&to={to_curr}"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            converted = data["rates"][to_curr]
            rate = converted / amount
            date = data["date"]
            
            return f"💱 {amount:,.2f} {from_curr} = {converted:,.2f} {to_curr}\n📊 Rate: 1 {from_curr} = {rate:.4f} {to_curr} (as of {date})"
        except Exception as e:
            return f"Currency conversion failed: {str(e)}"
    
    @kernel_function(
        name="GetExchangeRates",
        description="Get current exchange rates for a base currency."
    )
    def get_exchange_rates(
        self,
        base_currency: Annotated[str, "Base currency code (e.g., USD, EUR)"],
        target_currencies: Annotated[str, "Comma-separated target currencies"] = "EUR,GBP,JPY,INR,AUD,CAD"
    ) -> str:
        try:
            base = base_currency.upper()
            targets = target_currencies.upper()
            
            url = f"https://api.frankfurter.app/latest?from={base}&to={targets}"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            result = f"📊 Exchange Rates for 1 {base} (as of {data['date']}):\n"
            for currency, rate in data["rates"].items():
                result += f"  • {currency}: {rate:.4f}\n"
            
            return result
        except Exception as e:
            return f"Could not fetch exchange rates: {str(e)}"


class WorldTimePlugin:
    """Real world time data from worldtimeapi.org."""
    
    TIMEZONE_MAP = {
        "new york": "America/New_York",
        "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "seattle": "America/Los_Angeles",
        "denver": "America/Denver",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "dubai": "Asia/Dubai",
        "mumbai": "Asia/Kolkata",
        "singapore": "Asia/Singapore",
        "hong kong": "Asia/Hong_Kong",
    }
    
    @kernel_function(
        name="GetWorldTime",
        description="Get the current REAL time in any major city."
    )
    def get_world_time(
        self,
        city: Annotated[str, "City name (e.g., 'Tokyo', 'New York', 'London')"]
    ) -> str:
        try:
            city_lower = city.lower()
            timezone = self.TIMEZONE_MAP.get(city_lower)
            
            if not timezone:
                return f"Timezone not found for {city}. Try: New York, London, Tokyo, Paris, Sydney, Dubai, Mumbai"
            
            url = f"http://worldtimeapi.org/api/timezone/{timezone}"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            datetime_str = data["datetime"]
            utc_offset = data["utc_offset"]
            
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%I:%M:%S %p")
            formatted_date = dt.strftime("%A, %B %d, %Y")
            
            return f"🕐 {city.title()}: {formatted_time}\n📅 {formatted_date}\n🌐 UTC Offset: {utc_offset}"
        except Exception as e:
            return f"Could not fetch time for {city}: {str(e)}"


class QuotesPlugin:
    """Inspirational quotes from zenquotes.io API."""
    
    @kernel_function(
        name="GetRandomQuote",
        description="Get a random inspirational quote."
    )
    def get_random_quote(self) -> str:
        try:
            url = "https://zenquotes.io/api/random"
            with httpx.Client(timeout=10.0, verify=True) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            # zenquotes returns a list with one quote object
            quote_obj = data[0] if isinstance(data, list) else data
            quote = quote_obj.get("q", "No quote available")
            author = quote_obj.get("a", "Unknown")
            
            return f'💭 "{quote}"\n   — {author}'
        except Exception as e:
            return f"Could not fetch quote: {str(e)}"
    
    @kernel_function(
        name="GetQuoteByTag",
        description="Get a motivational or inspirational quote. Note: specific categories are not available, returns a random inspirational quote."
    )
    def get_quote_by_tag(
        self,
        tag: Annotated[str, "Quote category (returns random inspirational quote)"]
    ) -> str:
        # zenquotes doesn't support tags, so we get a random quote
        return self.get_random_quote()


class JokesPlugin:
    """Random jokes from Official Joke API."""
    
    @kernel_function(
        name="GetRandomJoke",
        description="Get a random joke."
    )
    def get_random_joke(self) -> str:
        try:
            url = "https://official-joke-api.appspot.com/random_joke"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            return f"😄 {data['setup']}\n\n🎯 {data['punchline']}"
        except Exception as e:
            return f"Could not fetch joke: {str(e)}"
    
    @kernel_function(
        name="GetProgrammingJoke",
        description="Get a programming/tech joke."
    )
    def get_programming_joke(self) -> str:
        try:
            url = "https://official-joke-api.appspot.com/jokes/programming/random"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()[0]
            
            return f"💻 {data['setup']}\n\n🎯 {data['punchline']}"
        except Exception as e:
            return f"Could not fetch programming joke: {str(e)}"


class WikipediaPlugin:
    """Quick facts from Wikipedia API."""
    
    @kernel_function(
        name="GetWikipediaSummary",
        description="Get a quick summary about any topic from Wikipedia."
    )
    def get_summary(
        self,
        topic: Annotated[str, "The topic to look up"]
    ) -> str:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            
            title = data.get("title", topic)
            extract = data.get("extract", "No summary available.")
            
            if len(extract) > 500:
                extract = extract[:500] + "..."
            
            return f"📚 {title}\n\n{extract}"
        except Exception as e:
            return f"Could not fetch Wikipedia summary for '{topic}': {str(e)}"


class FinancePlugin:
    """Financial calculation utilities."""
    
    @kernel_function(
        name="CalculateTip",
        description="Calculate tip amount and total bill."
    )
    def calculate_tip(
        self,
        bill_amount: Annotated[float, "The bill amount before tip"],
        tip_percentage: Annotated[float, "The tip percentage (e.g., 15, 18, 20)"]
    ) -> str:
        tip = bill_amount * (tip_percentage / 100)
        total = bill_amount + tip
        return f"🧾 Bill: ${bill_amount:.2f}\n💵 Tip ({tip_percentage}%): ${tip:.2f}\n💰 Total: ${total:.2f}"
    
    @kernel_function(
        name="SplitBill",
        description="Split a bill among multiple people with tip."
    )
    def split_bill(
        self,
        total_amount: Annotated[float, "The total bill amount"],
        num_people: Annotated[int, "Number of people to split among"],
        tip_percentage: Annotated[float, "Tip percentage to add"] = 0
    ) -> str:
        tip = total_amount * (tip_percentage / 100)
        total_with_tip = total_amount + tip
        per_person = total_with_tip / num_people
        return f"🧾 Subtotal: ${total_amount:.2f}\n💵 Tip ({tip_percentage}%): ${tip:.2f}\n💰 Total: ${total_with_tip:.2f}\n👥 Per person ({num_people}): ${per_person:.2f}"
    
    @kernel_function(
        name="CalculateCompoundInterest",
        description="Calculate investment growth with compound interest."
    )
    def calculate_compound_interest(
        self,
        principal: Annotated[float, "Initial investment amount"],
        annual_rate: Annotated[float, "Annual interest rate as percentage"],
        years: Annotated[int, "Number of years to invest"],
        compounds_per_year: Annotated[int, "Times interest compounds per year"] = 12
    ) -> str:
        rate = annual_rate / 100
        final_amount = principal * ((1 + rate/compounds_per_year) ** (compounds_per_year * years))
        earnings = final_amount - principal
        return (
            f"📈 Investment Calculator\n"
            f"💵 Initial: ${principal:,.2f}\n"
            f"📊 Rate: {annual_rate}% (compounded {compounds_per_year}x/year)\n"
            f"⏱️ Duration: {years} years\n"
            f"💰 Final Value: ${final_amount:,.2f}\n"
            f"✨ Total Earnings: ${earnings:,.2f}"
        )
    
    @kernel_function(
        name="CalculateLoanPayment",
        description="Calculate monthly loan/mortgage payment."
    )
    def calculate_loan_payment(
        self,
        principal: Annotated[float, "Loan amount"],
        annual_rate: Annotated[float, "Annual interest rate as percentage"],
        years: Annotated[int, "Loan term in years"]
    ) -> str:
        monthly_rate = (annual_rate / 100) / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            monthly_payment = principal / num_payments
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        total_paid = monthly_payment * num_payments
        total_interest = total_paid - principal
        
        return (
            f"🏠 Loan Calculator\n"
            f"💵 Loan Amount: ${principal:,.2f}\n"
            f"📊 Interest Rate: {annual_rate}%\n"
            f"⏱️ Term: {years} years ({num_payments} payments)\n"
            f"📅 Monthly Payment: ${monthly_payment:,.2f}\n"
            f"💰 Total to Pay: ${total_paid:,.2f}\n"
            f"📈 Total Interest: ${total_interest:,.2f}"
        )


class TaskManagerPlugin:
    """Task management plugin."""
    
    _tasks = []
    _next_id = 1
    
    def __init__(self):
        if not TaskManagerPlugin._tasks:
            TaskManagerPlugin._tasks = [
                {"id": 1, "task": "Review quarterly report", "priority": "high", "due": "today", "done": False},
                {"id": 2, "task": "Team standup meeting", "priority": "medium", "due": "today", "done": False},
                {"id": 3, "task": "Update project documentation", "priority": "low", "due": "tomorrow", "done": False},
            ]
            TaskManagerPlugin._next_id = 4
    
    @kernel_function(
        name="GetTasks",
        description="Get all tasks, optionally filtered."
    )
    def get_tasks(
        self,
        filter_by: Annotated[str, "Filter: 'all', 'today', 'pending', 'done', 'high', 'medium', 'low'"] = "all"
    ) -> str:
        tasks = TaskManagerPlugin._tasks
        
        if filter_by == "today":
            tasks = [t for t in tasks if t["due"] == "today"]
        elif filter_by == "pending":
            tasks = [t for t in tasks if not t["done"]]
        elif filter_by == "done":
            tasks = [t for t in tasks if t["done"]]
        elif filter_by in ["high", "medium", "low"]:
            tasks = [t for t in tasks if t["priority"] == filter_by]
        
        if not tasks:
            return f"📋 No tasks found for filter: {filter_by}"
        
        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        result = f"📋 Tasks ({filter_by}):\n"
        for t in tasks:
            status = "✅" if t["done"] else "⬜"
            icon = priority_icons.get(t["priority"], "⚪")
            result += f"  {status} [{t['id']}] {icon} {t['task']} (Due: {t['due']})\n"
        return result
    
    @kernel_function(
        name="AddTask",
        description="Add a new task."
    )
    def add_task(
        self,
        task: Annotated[str, "Task description"],
        priority: Annotated[str, "Priority: high, medium, or low"] = "medium",
        due: Annotated[str, "Due date"] = "today"
    ) -> str:
        new_task = {
            "id": TaskManagerPlugin._next_id,
            "task": task,
            "priority": priority.lower(),
            "due": due,
            "done": False
        }
        TaskManagerPlugin._tasks.append(new_task)
        TaskManagerPlugin._next_id += 1
        return f"✅ Task added: [{new_task['id']}] {task} (Priority: {priority}, Due: {due})"
    
    @kernel_function(
        name="CompleteTask",
        description="Mark a task as complete by ID."
    )
    def complete_task(
        self,
        task_id: Annotated[int, "The ID of the task to complete"]
    ) -> str:
        for t in TaskManagerPlugin._tasks:
            if t["id"] == task_id:
                t["done"] = True
                return f"✅ Completed: {t['task']}"
        return f"❌ Task with ID {task_id} not found"


# ============================================================================
# KERNEL SETUP
# ============================================================================

kernel: Optional[Kernel] = None

def create_kernel() -> Kernel:
    """Create and configure the Semantic Kernel with all plugins."""
    # Load .env from code-samples directory if not found locally
    load_dotenv()
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        # Try loading from code-samples directory (two levels up from backend)
        code_samples_env = os.path.join(os.path.dirname(__file__), "..", "..", "code-samples", ".env")
        load_dotenv(code_samples_env)
    
    k = Kernel()
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    credential = AzureCliCredential(tenant_id=tenant_id) if tenant_id else AzureCliCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    
    k.add_service(
        AzureChatCompletion(
            service_id="default",
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_COMPLETION_MODEL"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            ad_token_provider=token_provider
        )
    )
    
    # Register all plugins
    k.add_plugin(WeatherPlugin(), "Weather")
    k.add_plugin(CurrencyPlugin(), "Currency")
    k.add_plugin(WorldTimePlugin(), "WorldTime")
    k.add_plugin(QuotesPlugin(), "Quotes")
    k.add_plugin(JokesPlugin(), "Jokes")
    k.add_plugin(WikipediaPlugin(), "Wikipedia")
    k.add_plugin(FinancePlugin(), "Finance")
    k.add_plugin(TaskManagerPlugin(), "Tasks")
    
    return k


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize kernel on startup."""
    global kernel
    kernel = create_kernel()
    yield


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Personal Assistant API",
    description="AI-powered personal assistant with real-time data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the assistant."""
    global kernel
    
    if not kernel:
        raise HTTPException(status_code=500, detail="Kernel not initialized")
    
    try:
        arguments = KernelArguments(
            settings=PromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
            )
        )
        
        result = await kernel.invoke_prompt(request.message, arguments=arguments)
        
        return ChatResponse(
            response=str(result),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/capabilities")
async def get_capabilities():
    """Get list of available capabilities."""
    return {
        "capabilities": [
            {"name": "Weather", "icon": "🌤️", "description": "Live weather data for any city worldwide"},
            {"name": "Currency", "icon": "💱", "description": "Real-time exchange rates"},
            {"name": "World Time", "icon": "🕐", "description": "Current time in major cities"},
            {"name": "Quotes", "icon": "💭", "description": "Inspirational quotes by category"},
            {"name": "Jokes", "icon": "😄", "description": "Random jokes and programming humor"},
            {"name": "Wikipedia", "icon": "📚", "description": "Quick facts about any topic"},
            {"name": "Finance", "icon": "💰", "description": "Loans, investments, tips, bill splitting"},
            {"name": "Tasks", "icon": "📋", "description": "Manage your todo list"},
        ]
    }


# Serve static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
