# **🎶 Discord Music Bot**  

A **simple, lightweight, and feature-rich** Discord music bot built using **Python**, **lavalink** and `discord.py`.

## **🚀 Features**  
✔️ **Plays high-quality music** from **YouTube** and **spotify** (via `lavalink`)  
✔️ **Supports playlists and song queues**  
✔️ **Basic playback controls:** `play`, `pause`, `resume`, `skip`, `stop`  
✔️ **Volume control**  
✔️ **Loop single song or entire queue**  
✔️ **Auto-disconnect when idle**  
✔️ **Supports slash commands**  

---

## **🛠️  Installation**  

### **Prerequisites**  
- **Python 3.11+**  
- `discord.py` (`pip install discord.py`)  
- `wavelink` (`pip install wavelink`) *(Required for Lavalink integration)*
- `psutil` (`pip install psutil`)
- `aiohttp` (`pip install aiohttp`)
- **LavaLnk**


## 🎵 Lavalink Server Requirement

This bot requires a **Lavalink server** to function properly for music playback. You can either:

1. **Host your own Lavalink server**  
   - Download Lavalink from [GitHub](https://github.com/freyacodes/Lavalink)  
   - Install Java 17+ (`OpenJDK 17` recommended)  
   - Configure `application.yml` with your credentials  
   - Run Lavalink using:  
     ```sh
     java -jar Lavalink.jar
     ```

2. **Use a public Lavalink server** (Not recommended due to reliability concerns)  
   - Some providers offer public Lavalink nodes; ensure you get valid credentials.

### 🔑 Lavalink Configuration Example:
If hosting your own server, you need to set these credentials in your bot's configuration:

```yaml
server:
  port: 2333
lavalink:
  password: "your_password"
  rest_url: "http://localhost:2333"
  ws_url: "ws://localhost:2333"



### **\ud83d\udd39 Setup**  
1\ufe0f\u20e3 **Clone the repository:**  
```bash
git clone https://github.com/yourusername/discord-music-bot.git
cd discord-music-bot
```


2\ufe0f\u20e3 **Install dependencies:**  
```bash
pip install -r requirements.txt
```  
3\ufe0f\u20e3 **Add your bot token and lavalink credientials**  
```
DISCORD_BOT_TOKEN=your-bot-token-here
LAVALINK_HOST = ""  # Replace with actual Lavalink server
LAVALINK_PORT = 
LAVALINK_PASSWORD = ""  # Replace with your Lavalink password
```  
4\ufe0f\u20e3 **Run the bot:**  
```bash
python bot.py
```  

---

## **\ud83d\udcdd Commands**  
| **Command** | **Description** |
|------------|----------------|
| `/play [query]` | Play a song from YouTube/Spotify |
| `/nowplaying` | Show the currently playing track |
| `/queue` | View the current queue |
| `/skip` | Skip to the next track |
| `/playprevious` | Play the previously played song |
| `/pause` | Pause the current song |
| `/resume` | Resume paused music |
| `/stop` | Stop playback and clear the queue |
| `/clearqueue` | Remove all tracks from the queue |
| `/shuffle` | Shuffle the queue |
| `/loop [on/off]` | Toggle loop mode |
| `/volume [0-100]` | Adjust music volume |
| `/247 [on/off]` | Enable or disable 24/7 mode |

## 🛠 Utility Commands
| **Command** | **Description** |
|------------|----------------|
| `/ping` | Check bot latency & Lavalink ping |
| `/stats` | View bot statistics |
| `/invite` | Get the bot invite link |
| `/help` | Display this help menu |

---

## **🏆  Why Use This Bot?**  
🔹 **Lightweight & Fast** – Minimal resource usage  
🔹 **No Lag & Smooth Playback** – Optimized audio streaming  
🔹 **Easy to Customize** – Modify commands as per your needs  

---

## **🤝 Contributing**  
Feel free to **fork** this repository, make changes, and submit a **pull request**! 🚀
