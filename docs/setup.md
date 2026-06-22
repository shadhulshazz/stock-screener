# Setup Guide

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git
- Google Cloud Account (free tier)
- Telegram account & Bot Token
- Claude or Groq API key

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/shadhulshazz/stock-screener.git
cd stock-screener
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Test Locally

```bash
python screener.py --test --no-send
```

## API Keys Setup

### Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Create new bot: `/newbot`
3. Copy the token to `TELEGRAM_BOT_TOKEN` in `.env`
4. Get your chat ID:
   - Send a message to the bot
   - Visit: `https://api.telegram.org/bot{TOKEN}/getUpdates`
   - Copy `chat.id` to `TELEGRAM_CHAT_ID`

### Claude API

1. Visit https://console.anthropic.com
2. Create API key
3. Set `CLAUDE_API_KEY` in `.env`

### Groq API (Alternative)

1. Visit https://console.groq.com
2. Create API key
3. Set `GROQ_API_KEY` in `.env`
4. Set `AI_PROVIDER=groq` in `.env`

### Google Sheets (Optional)

1. Create Google Cloud Project
2. Enable Sheets API
3. Create Service Account credentials (JSON)
4. Download credentials file
5. Set `GOOGLE_SHEETS_CREDENTIALS` to file path
6. Set `GOOGLE_SHEETS_ID` to your sheet ID

## Running the Screener

### Test Mode

```bash
python screener.py --test --no-send
```

### Specific Stocks

```bash
python screener.py --symbols "INFY,TCS,RELIANCE" --no-send
```

### Full Mode (with Alerts)

```bash
python screener.py
```

## Troubleshooting

### No Data Fetched

- Check internet connection
- Verify stock symbols are correct (NSE format)
- yfinance may have temporary issues; retry later

### API Errors

- Verify API keys are correct
- Check rate limits (Claude: 100k tokens/min, Groq: varies)
- Ensure accounts have available credits

### Telegram Not Sending

- Verify bot token and chat ID
- Test: `curl -X GET https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Test`
