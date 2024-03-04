# ORB TelegramBot
Do you want to check the weather? Roll a die? Need text-to-speech or just want to have some fun? This is the bot for you!

Set up your own instance by following the step-by-step instructions in the [installation guide](https://github.com/archetipico/TelegramBot#installation).

# Commands
Legend for the following guide:
- `#` highlights the command in the list of commands
- `|` serves as a separator between commands, to be understood as OR
- `<...>` indicates the need to insert a specific type of data
- `[...]` is used for optional arguments
- `>` represents the concept of the executed command
- `!` is for comments

You don't need to include these symbols in the command; they are only used as markdown for this guide. Therefore, if, for example, you want to execute the command to clean a link, just type `clr` , and not `# clr`, or in the case without JavaScript, `clr -js`.

```markdown
# /help
Help
> /help                     ! Remember that it's the only command with a slash

# 8ball [<text>]
Shake a Magic 8 Ball in response to a text or by asking a question afterward
> 8ball
> 8ball Will tomorrow be a nice day?

# canny [-m] [<min> <max>]
Highlight the edges within photos
> canny                     ! Set to (50, 150) by default
> canny -m                  ! Mask image
> canny 60, 120
> canny -m 10, 100

# clr [-js]
(CLeaR) Cleanse the dirty URLs
> clr                       ! No more trackers
> clr -js                   ! No more JavaScript

# color <hex>
Convert the hexadecimal color code into the actual color name
> color 00ff44

# cpt [-f] <up>, <down>
(CaPTion) Create captions on images (PNG or JPEG), on GIFs and on videos
> cpt top, bottom           ! Classic
> cpt top text,             ! Top only
> cpt , bottom text         ! Bottom only
> cpt ,                     ! No effect
> cpt                       ! No effect
> cpt -f                    ! Make the media faster
> cpt -f top, bottom        ! Also make the media faster

# detect
Basic neural network to detect objects (80 distinct) and faces (underlined in green) in images
> detect                    ! It could take a while

# info
Informations about a message
> info

# kanji
Return a random kanji (Note: kanji symbols are added gradually as I learn them)
> kanji                     ! 果

# malus [show|<user>]|[add|rm <malus>]
Apply a random event to yourself or to a user by responding to their message or by tagging them
> malus
> malus add New malus I think is funny
> malus add earns [2:10] XP
> malus rm malus old malus I don't need anymore
> malus show
> malus @johndoe
> malus John Doe

# manuser add|rm
Answer to a user's message to add or remove them from the allowed users list
** Note: only superadmins can use this feature **
> manuser add               ! Respect gained
> manuser rm                ! Respect lost

# ocr [<language>]|[-l]
Given an image return the Optical Character Recognition
> ocr
> ocr chi_sim               ! Chinese simplified
> ocr it+fra                ! Italian and French
> ocr -l                    ! List all the supported languages

# oled [<white>]
Answer to an image to adapt it to an OLED screen: the `white` threshold defines when a pixel should be considered white
> oled                      ! Set to 127 by default
> oled 90
> oled 3280                 ! Modulo 256

# paint [<val>]
Paint effect on an image, GIF or MP4, possibly using a reference value <val>
> paint                     ! Set to 5 by default
> paint -1                  ! Passed to modulo 10

# palette [<n>]
Use it in response to a photo to receive the color palette used in the image
> palette                   ! Set to 5 by default
> palette 3
> palette 40                ! 1..10 is okay but this is passed as 5 (default)

# pixel [<val>]
Pixelate an image
> pixel                     ! Set to 50 by default
> pixel 5
> pixel 150                 ! Modulo 100

# rgx <regex>, <testo>
(ReGeX) Given a regex, apply a text substitution
> rgx [a-zA-Z].+, xyzzy

# relief [<n> <k>]
Show relief on images
> relief                    ! Set to (30 2) by default
> relief 15 4

# rev [-l]
(REVerse) Invert video and audio of GIF, MOV, MP3, MP4, OGG, WEBM (commonly animated stickers on Telegram) and various formats files
> rev
> rev list                  ! List all the supported formats

# roll [<n>]
Roll a <n>-sided die
> roll                      ! Set to 6 by default
> roll 20                   ! DnD gamers rise up
> roll 30                   ! It seems they exist
> roll -1                   ! You will be mocked

# scale [<val>]
Scale an image, GIF or MP4 using the Liquid Rescaling technique, possibly using a reference value <val>
> scale                     ! Set to 50 by default
> scale 25
> scale 1                   ! Goodbye
> scale -1                  ! 1..100 is okay but this is passed as 50 (default)

# solve <math>
Solve anything in mathematical language
> solve 1 + 1
> solve 6 feet to m
> solve 1/(x^2+2x−3) to partial fraction
> solve life issues         ! Unfortunately we must solve our own problems

# stats [self]
Show commands usage: "Failure" does not refer to the person using the command
> stats
> stats self                ! Your statistics

# strip [-l]
Remove metadata and attempt to reduce the size of specific files
> strip
> strip -l                  ! List all the supported formats

# tts [<language> [<text>]]|[-l]
(Text-To-Speech) Read the <text> in the selected language (when responding to a message, <text> is the message being replied to)
> tts                       ! Set to 'en' by default
> tts -l                    ! List all the supported languages
> tts it Ciao gente         ! Hello

# urb <search>
Search on the Urban Dictionary
> urb most deranged thing ever

# wtr <location>
(WeaTheR) Given a location, provide real-time and highly detailed weather information
> wtr London
> wtr 東京
> wtr unknown place         ! 99.9% of the time it finds it
> wtr my fav pub            ! If it's in the database it will find that too

# xkcd
Classic nerd puns
> xkcd
```

# Installation
## Preamble
As a first step, it is necessary to generate the files that will contain the information required for the correct operation of the bot. When possible, the required software will also be installed, as listed at the end of the README. Below you will find a guide for Linux users and a guide for Windows users. Regardless of your operating system, the execution should be successful; if not, feel free to open an issue.

### Linux
- Make sure you have `wget` installed (run `wget --version`)
- In the main folder, you will find `preamble.sh`
- Execute `chmod 755 preamble.sh`
- Then run `./preamble.sh` to download the necessary files

### Windows
Note:
In addition to the required software [Chocolatey](https://chocolatey.org/) will also be installed.
- Open a PowerShell terminal as an administrator
- Remember that you may need to run `Set-ExecutionPolicy RemoteSigned`
- In the main folder, you will find `preamble.ps1`
- Execute `.\preamble.ps1` to download the necessary files and install the required dependencies

## Key generation
- Register on [OpenWeatherMap](https://openweathermap.org) and obtain a free API key
- Generate a key for a Telegram bot by contacting [@BotFather](https://t.me/BotFather)
- Go into the subfolder `./orders/utility` and modify the `secrets` file
- The first line of the file should be the OpenWeatherMap key
- The second line of the file should be the Telegram key
- Leave an empty line at the end as per the standard so that running `cat secrets` does not have an extra newline but also doesn't cause the terminal line to wrap
- For example, the file should look like this:
```markdown
OWM-KEY
TELEGRAM-KEY

```
- The `cat secrets` command should then display the following:
```markdown
[user@machine]:~/TelegramBot/orders/utility $ cat secrets
OWM-KEY
TELEGRAM-KEY
[user@machine]:~/TelegramBot/orders/utility $
```

Note:
It may not be necessary to insert an empty line at the end of the text; it depends on many factors. However, remember this convention for the following steps as it is essential for the correct reading and writing of files.

## Populate administrative files
- Go into the subfolder `./orders/utility` and modify the `superadmins` file
- Insert your Telegram user ID following the previous text formatting convention
- If you don't know your Telegram user ID, you can write a short line of code inside `bot.py` to print your user ID, as follows:
```python
# You can find this function inside bot.py and write it at the first line
async def msg_filter( ... ):
    print(update.effective_chat.id)
```
- Now, send a message to the bot privately, and it will print your ID to the terminal. Alternatively, you can contact a bot like `@userinfobot` (I haven't tested it, but it's commonly suggested)
- Once you have obtained your ID and added it to `superadmins`, add your ID to `admins` as well, following the convention
- If you want to allow other users to use your bot, you can do so by adding the bot to a group with the interested user and by typing `manuser add` in response to a message from the user you want to promote

## Python dependencies
- The bot has been programmed with `Python 3.9.2`
- Install the requirements found in `requirements.txt`
- Execute `pip install "python-telegram-bot[job-queue]"`
- Execute `pip install "python-telegram-bot[http2]"`

## Other dependencies to install
Below is the list of software necessary to use the bot commands, all installable from the command line. Depending on the OS, some of them are already installed.
#### Linux
- [ExifTool](https://exiftool.org/)
- [FFmpeg](https://ffmpeg.org/)
- [Ghostscript](https://www.ghostscript.com/)
- [ImageMagick](https://imagemagick.org/)
- [jpegoptim](https://github.com/tjko/jpegoptim)
- [OptiPNG](https://optipng.sourceforge.net/)
- [Qalculate](https://qalculate.github.io/)
- [Tesseract](https://tesseract-ocr.github.io/)
#### Windows
- [Tesseract](https://tesseract-ocr.github.io/)

## Execution
You can run the bot by executing `python bot.py` from the terminal. Alternatively, if you want the bot to start on machine startup (on Linux), type `crontab -e` and insert the following text string:
```bash
@reboot python ~/your_path/TelegramBot/bot.py > ~/your_path/TelegramBot/out 2>&1
```

# Third-party software used
Here is the list of projects used, many thanks to them:
- API calls
  - https://openweathermap.org
  - https://operations.osmfoundation.org
- Non-API calls
  - https://www.colorhexa.com
  - https://www.urbandictionary.com
  - https://xkcd.com
- Software
  - https://exiftool.org/
  - https://ffmpeg.org/
  - https://www.ghostscript.com/
  - https://github.com/AlexeyAB/darknet/
  - https://github.com/ClearURLs/Rules - personal version
  - https://github.com/jcsirot/kanji.gif/
  - https://github.com/scour-project/scour
  - https://github.com/tjko/jpegoptim
  - https://imagemagick.org/
  - https://optipng.sourceforge.net/
  - https://qalculate.github.io/
  - https://tesseract-ocr.github.io/
