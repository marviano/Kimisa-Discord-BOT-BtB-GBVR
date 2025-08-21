## Kimisa Discord Bot — GBVSR Frame Data

Kimisa is a Discord bot that fetches Granblue Fantasy Versus: Rising (GBVSR) move and frame data from the Dustloop wiki and posts formatted results in your server. It includes embeds for images/hitboxes where available, readable text formatting, a short cooldown to prevent spam, and a debug helper to explore a character’s move structure.

### Features
- **Frame data lookup**: `!kimi <character> <section> <move>`
- **Helpful formatting**: Cleaned text, lists, and highlighted move notations
- **Embeds for images**: Shows standard and hitbox images when available
- **Cooldown**: 3s per-user cooldown to reduce spam
- **Debug mode**: Explore a character page’s sections and moves

### Commands
- **Help**: `!kimi help`
  - Shows usage, sections, and examples
- **Lookup**: `!kimi <character> <section> <move>`
  - Sections: `normal`, `dash`, `air`, `unique`, `skill`
  - Examples:
    - `!kimi Zeta normal c.L`
    - `!kimi Gran dash 66H`
    - `!kimi Charlotta air j.M`
- **Debug**: `!kimi-debug <character>`
  - Prints sections and discovered moves for the character

### Requirements
- Node.js 18+
- Python 3.11+ (tested) with packages:
  - `requests`
  - `beautifulsoup4`
- A Discord bot with the following intents enabled in the Developer Portal:
  - `Server Members Intent` (optional, not required by current code)
  - `Message Content Intent` (required)

### Installation
1. Clone this repository.
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Install Python dependencies:
   ```bash
   pip install requests beautifulsoup4
   ```

### Configuration
Create a `.env` file in the project root:
```env
TOKEN=your_discord_bot_token_here
# Optional: set to true to forward Python stderr as debug messages in Discord
DEBUG_MODE=false
```

Windows-specific note: `bot.js` currently calls Python via a hard-coded path:
```js
const pythonPath = 'C:\\Users\\Austin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe';
```
Update this path to your Python executable, or change the code to call `python` (or `py -3`) from PATH if you prefer. Example alternative:
```js
const pythonPath = 'python';
```

### Run the Bot
```bash
node bot.js
```
You should see “Bot is online!” in your console. In Discord, try:
```text
!kimi help
!kimi Zeta normal c.L
!kimi Gran dash 66H
```

### How It Works
- `bot.js` (Node, `discord.js@14`) receives commands, throttles users (3s cooldown), and invokes Python.
- `scraper.py` fetches and parses `https://www.dustloop.com/w/GBVSR/<Character>` for the specified section and move, returning structured JSON for the bot to format.
- `scraper-debug.py` prints a character’s sections/moves to help you discover valid inputs.
- A `scraper.log` file is written with logs from Python scraping.

### Common Sections and Move Inputs
- Sections accepted (normalized internally): `Normal Moves`, `Dash Normals`, `Air Normals`, `Unique Action`, `Skills` (you can pass `normal`, `dash`, `air`, `unique`, `skill`).
- Moves may be written in common notation and are normalized, e.g. `c.L`, `f.M`, `2H`, `j.U`, `66H`, `236L`, etc. Some special moves are mapped to their names (e.g., Dream Attraction → `236L`).

### Troubleshooting
- **No response / errors**: Ensure the bot token is correct, intents are enabled, and the bot is in your server.
- **Python not found**: Update the `pythonPath` in `bot.js` or ensure `python`/`py` is in PATH. Verify `pip install requests beautifulsoup4`.
- **Move not found**: Use `!kimi-debug <character>` to explore available sections/moves, and try the normalized names shown there.
- **Rate-limiting**: The bot has a 3s per-user cooldown. Wait and retry.
- **Connection issues**: The scraper uses requests with a timeout and may fail if Dustloop is slow/unreachable. Try again later.
- **Long messages**: The bot automatically splits long messages to fit Discord’s limits.

### Project Structure
```text
bot.js                # Discord bot (Node + discord.js)
scraper.py            # Dustloop scraper (Python)
scraper-debug.py      # Debug helper to list sections/moves (Python)
scraper.log           # Python scraper log output
package.json          # Node dependencies (discord.js, dotenv)
.env                  # Discord bot token and debug flag (not committed)
privacypolicy.txt     # Privacy policy for this bot
tos.txt               # Terms of service
LICENSE               # MIT License
```

### Privacy and Terms
- See `privacypolicy.txt` for how we handle data.
- See `tos.txt` for terms of service.

### License
This project is licensed under the MIT License. See `LICENSE` for details.

### Credits and Data Source
- Data sourced from the Dustloop wiki. Please support and respect their community guidelines.


