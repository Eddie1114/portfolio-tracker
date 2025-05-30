from openai import AsyncOpenAI
from app.core.config import settings
from typing import List, Dict, Any
import json
import openai
from datetime import datetime, timedelta

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_portfolio_insights(portfolio_data: Dict) -> Dict:
    """Generate AI-powered insights for the portfolio"""
    try:
        # Prepare portfolio summary
        holdings_summary = "\n".join([
            f"- {holding['symbol']}: ${holding['current_value']:,.2f} "
            f"({holding['gain_loss_percentage']:.1f}% return)"
            for holding in portfolio_data['holdings']
        ])
        
        diversification_summary = (
            f"Portfolio has {portfolio_data['diversification']['number_of_holdings']} holdings. "
            f"Top holdings: " + ", ".join([
                f"{h['symbol']} ({h['percentage']:.1f}%)"
                for h in portfolio_data['diversification']['top_holdings']
            ])
        )
        
        # Generate insights using OpenAI
        prompt = f"""
        Analyze this investment portfolio and provide insights:
        
        Portfolio Summary:
        Total Value: ${portfolio_data['total_value']:,.2f}
        {holdings_summary}
        
        Diversification:
        {diversification_summary}
        
        Please provide:
        1. Key portfolio strengths and concerns
        2. Diversification recommendations
        3. Potential opportunities based on current market conditions
        4. Risk assessment
        5. Suggested actions for portfolio optimization
        
        Format the response as a structured JSON with these sections.
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a professional portfolio analyst providing insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse and structure the AI response
        insights = response.choices[0].message.content
        
        # Generate market sentiment analysis
        sentiment = await analyze_market_sentiment(portfolio_data['holdings'])
        
        return {
            "portfolio_analysis": insights,
            "market_sentiment": sentiment,
            "generated_at": datetime.utcnow().isoformat(),
            "next_review_recommended": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to generate portfolio insights: {str(e)}",
            "generated_at": datetime.utcnow().isoformat()
        }

async def analyze_market_sentiment(holdings: List[Dict]) -> Dict:
    """Analyze market sentiment for portfolio holdings"""
    try:
        symbols = [holding['symbol'] for holding in holdings]
        symbols_str = ", ".join(symbols)
        
        prompt = f"""
        Analyze current market sentiment and trends for these stocks: {symbols_str}
        
        Consider:
        1. Recent market news and events
        2. Industry trends
        3. Technical indicators
        4. Market sentiment indicators
        
        Provide a structured analysis with sentiment scores and key factors.
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a market sentiment analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        sentiment_analysis = response.choices[0].message.content
        
        return {
            "sentiment_analysis": sentiment_analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to analyze market sentiment: {str(e)}",
            "analyzed_at": datetime.utcnow().isoformat()
        }

async def analyze_transaction_history(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze transaction history to identify patterns and provide recommendations.
    """
    # Prepare transaction data for the prompt
    transaction_summary = []
    for tx in transactions:
        summary = (
            f"{tx['transaction_type'].upper()}: {tx['asset_symbol']} "
            f"Quantity: {tx['quantity']}, Price: ${tx['price']:.2f}, "
            f"Date: {tx['timestamp']}"
        )
        transaction_summary.append(summary)
    
    transactions_text = "\n".join(transaction_summary)
    
    prompt = f"""Analyze the following trading history and provide insights:

Transaction History:
{transactions_text}

Please provide:
1. Trading Patterns Analysis
2. Performance Metrics
3. Behavioral Insights
4. Improvement Recommendations
5. Market Timing Analysis

Format the response as JSON with these sections as keys."""

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional trading analyst providing transaction insights."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    
    try:
        insights = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        insights = {
            "error": "Failed to parse AI response",
            "raw_response": response.choices[0].message.content
        }
    
    return insights 