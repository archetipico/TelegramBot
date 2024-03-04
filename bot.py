from colorama import Fore, init
from cv2 import CascadeClassifier, FONT_HERSHEY_SIMPLEX, LINE_AA
from cv2.data import haarcascades
from cv2.dnn import DNN_BACKEND_OPENCV, DNN_TARGET_CPU, readNet
from json import load
from order import Order
from orders.urban import Urban
from orders.weather import Weather
from os import chdir, environ, getcwd, getpid, path, remove, system, walk
from pathlib import Path
from platform import system
from secret import Secret
from shutil import which
from subprocess import run
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters


# Helper
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            "Press the button to see the commands",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="Commands",
                    web_app=WebAppInfo(url="https://github.com/archetipico/TelegramBot/blob/master/README.md"),
                )
            )
        )
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='For a better view, I recommend typing /help in private!\n\n'
                 'https://github.com/archetipico/TelegramBot/blob/master/README.md',
            parse_mode='HTML'
        )


# Filter messages
async def msg_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global admins

    msg = update.effective_message
    order = Order(msg, wd, keys, exec_paths, deep_nn, classifiers, rules, kanji_list, font_params).run_order()

    # If there are no orders
    if order is None:
        return

    # If there was a manuser operation I have to reload "admins"
    command = msg.text.split(' ', 1)[0].lower()
    if command == 'manuser':
        admins = Secret(wd).get_key('admin')

    bot = context.bot
    chat = update.effective_chat.id

    try:
        send = order.get('send')
        order_type = order.get('type')
        # Types of orders and responses
        order_types = {
            'animation': bot.send_animation,
            'document': bot.send_document,
            'photo': bot.send_photo,
            'text': bot.send_message,
            'video_note': bot.send_video_note,
            'voice': bot.send_voice
        }

        # If it has to answer
        if order_type in order_types:
            # If it's text response
            if order_type == 'text':
                # If it's weather
                if command == 'wtr':
                    bot_msg = await order_types[order_type](
                        chat_id=chat,
                        text=send,
                        reply_to_message_id=order.get('msg_id'),
                        parse_mode='HTML',
                        reply_markup=order.get('reply_markup')
                    )

                    context.user_data['msg_id'] = bot_msg.message_id
                    context.user_data['user_id'] = msg.from_user.id
                    context.user_data['msg'] = msg
                    context.user_data['forecast'] = 3
                # If it's urban
                elif command == 'urb':
                    bot_msg = await order_types[order_type](
                        chat_id=chat,
                        text=send,
                        reply_to_message_id=order.get('msg_id'),
                        parse_mode='HTML',
                        reply_markup=order.get('reply_markup')
                    )

                    # Initialize the context
                    context.user_data['msg_id'] = bot_msg.message_id
                    context.user_data['user_id'] = msg.from_user.id
                    context.user_data['msg'] = msg
                    context.user_data['idx'] = 1
                else:
                    await order_types[order_type](
                        chat_id=chat,
                        text=send,
                        reply_to_message_id=order.get('msg_id'),
                        parse_mode='HTML'
                    )
            # If it's video note
            elif order_type == 'video_note':
                await order_types[order_type](
                    chat_id=chat,
                    **{order_type: send},
                    filename=order.get('filename'),
                    reply_to_message_id=order.get('msg_id')
                )
            # If it's not text response
            else:
                await order_types[order_type](
                    chat_id=chat,
                    **{order_type: send},
                    filename=order.get('filename'),
                    reply_to_message_id=order.get('msg_id'),
                    caption=order.get('caption'),
                    parse_mode='HTML'
                )

        # Delete message if asked by command
        if order.get('destroy'):
            await bot.delete_message(
                chat_id=chat,
                message_id=msg.message_id
            )

        # Clean tmp files if asked by command (privacy reasons)
        if order.get('privacy'):
            directory = str(Path(wd).joinpath('orders', 'tmp'))
            for root, dirs, files in walk(directory):
                for file in files:
                    if file != '.empty':
                        remove(str(Path(root).joinpath(file)))
    except Exception as exc:
        await bot.send_message(
            chat_id=chat,
            text='Errore:\n{}'.format(str(exc)),
            reply_to_message_id=None,
            parse_mode='HTML'
        )


# Update messages if they have InlineKeyboard
async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Use the globally defined context_queries
    global context_queries

    # Check if there's a previous msg_id associated with this command
    prev_command = [i for i in context_queries if i['user_id'] == context.user_data['user_id']]
    # If there is one, stop the callback query there
    if prev_command:
        # Remove prev_command from context_queries
        context_queries = [i for i in context_queries if i not in prev_command]
        # Remove the inline keyboard from the old message
        if prev_command[0]['msg_id'] != context.user_data['msg_id']:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                text=prev_command[0]['content'],
                message_id=prev_command[0]['msg_id'],
                parse_mode='HTML',
                reply_markup=None
            )

    query = update.callback_query
    btn_data = query.data
    await query.answer()

    # Update the message based on the btn click
    if btn_data == 'next_wtr':
        res = Weather(context.user_data['msg'], owm, forecast=context.user_data['forecast']).get()

        # Edit the message with the updated content
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=res.get('send'),
            message_id=context.user_data['msg_id'],
            parse_mode='HTML',
            reply_markup=res.get('reply_markup')
        )

        context_query = {
            'msg_id': context.user_data['msg_id'],
            'user_id': context.user_data['user_id'],
            'content': res.get('send')
        }

        context_queries.append(context_query)

        context.user_data['forecast'] += 3
    elif btn_data == 'next_urb':
        res = Urban(context.user_data['msg'], idx=context.user_data['idx']).get()

        # Edit the message with the updated content
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=res.get('send'),
            message_id=context.user_data['msg_id'],
            parse_mode='HTML',
            reply_markup=res.get('reply_markup')
        )

        context_query = {
            'msg_id': context.user_data['msg_id'],
            'user_id': context.user_data['user_id'],
            'content': res.get('send')
        }
        context_queries.append(context_query)

        context.user_data['idx'] += 1


if __name__ == '__main__':
    try:
        # COLORAMA INIT
        init()
        print('{}----- INITIALIZATION PROCESS -----{}'.format(Fore.GREEN, Fore.RESET))

        # CPU AFFINITY
        try:
            system('taskset -p 0xffffffff %d > /dev/null 2>&1' % getpid())
            print('{}>{} CPU affinity set'.format(Fore.BLUE, Fore.RESET))
        except Exception:
            print('{}>{} Using OS-default CPU affinity'.format(Fore.BLUE, Fore.RESET))

        # SETTING WORKING DIRECTORY
        chdir(path.dirname(path.abspath(__file__)))
        wd = getcwd()
        print('{}>{} Working directory set as: {}'.format(Fore.BLUE, Fore.RESET, wd))

        # CLEAN ANY GARBAGE
        directory = str(Path(wd).joinpath('orders', 'tmp'))
        for root, dirs, files in walk(directory):
            for file in files:
                if file != '.empty':
                    remove(str(Path(root).joinpath(file)))
        print('{}>{} Took the trash out'.format(Fore.BLUE, Fore.RESET))

        # KEYS RETRIEVAL
        secret = Secret(wd)
        superadmins = secret.get_key('superadmin')
        admins = secret.get_key('admin')
        key = secret.get_key('telegram')
        owm = secret.get_key('owm')
        keys = (superadmins, admins, key, owm)
        print('{}>{} Keys retrieved'.format(Fore.BLUE, Fore.RESET))

        # INTEGRITY OF EXECUTABLES PATHS
        sys = system()
        print('{}>{} System detected: {}'.format(Fore.BLUE, Fore.RESET, sys))
        # Environments for Linux
        if sys == 'Linux':
            environ['PATH'] = '/usr/local/bin:/usr/bin:' + environ['PATH']
            print('{}>{} Environment set'.format(Fore.BLUE, Fore.RESET))

            # All the softwares used
            exec_paths = {
                'exiftool': None,
                'ffmpeg': None,
                'gs': None,
                'mogrify': None,
                'jpegoptim': None,
                'optipng': None,
                'qalc': None,
                'tesseract': None
            }

            # Update qalculate exchange rates if needed
            result = run(['bash', wd + '/orders/utility/update_exchange_rates.sh'], capture_output=True, text=True)
            if result.returncode == 0:
                print('{}>{} Exchange rates updated'.format(Fore.BLUE, Fore.RESET))
            else:
                print('{}> Exchange rates not updated{}'.format(Fore.RED, Fore.RESET))
        # Environments for Windows
        else:
            # All the softwares used
            exec_paths = {
                'exiftool': None,
                'ffmpeg': None,
                'gswin64c': None,
                'magick mogrify': None,
                'jpegoptim': None,
                'optipng': None,
                'qalc': None,
                'tesseract': None
            }

            # Update qalculate exchange rates if needed
            result = run(['powershell', '-File', wd + '/orders/utility/update_exchange_rates.ps1'], capture_output=True, text=True)
            if result.returncode == 0:
                print('{}>{} Exchange rates updated'.format(Fore.BLUE, Fore.RESET))
            else:
                print('{}> Exchange rates not updated{}'.format(Fore.RED, Fore.RESET))
        # Fill the paths
        for e in exec_paths.keys():
            path = which(e)
            if path:
                exec_paths[e] = str(path)
                print('{}>{} Installation for \'{}\' found at {}'.format(Fore.BLUE, Fore.RESET, e, path))
            else:
                print('{}> {} is not installed or the path cannot be found{}'.format(Fore.RED, e, Fore.RESET))
        # Unify the paths for bot usage in case Windows was detected
        if sys != 'Linux':
            tmp_paths = {
                'exiftool': exec_paths['exiftool'],
                'ffmpeg': exec_paths['ffmpeg'],
                'gs': exec_paths['gswin64c'],
                'mogrify': exec_paths['magick mogrify'],
                'jpegoptim': exec_paths['jpegoptim'],
                'optipng': exec_paths['optipng'],
                'qalc': exec_paths['qalc'],
                'tesseract': exec_paths['tesseract']
            }

            exec_paths = tmp_paths

        # NEURAL NETWORK OBJECT DETECTION PRE-LOADING
        # Load the pre-trained YOLO model
        net = readNet(
            '{}/orders/utility/yolov4-tiny.weights'.format(wd),
            '{}/orders/utility/yolov4-tiny.cfg'.format(wd)
        )
        # Specify the preferred target backend and target
        net.setPreferableBackend(DNN_BACKEND_OPENCV)
        net.setPreferableTarget(DNN_TARGET_CPU)
        # Load the COCO class labels on which the YOLO model was trained
        with open('{}/orders/utility/coco.names'.format(wd), 'r') as f:
            classes = [line.strip() for line in f.readlines()]
        deep_nn = (net, classes)
        print('{}>{} Built DNN'.format(Fore.BLUE, Fore.RESET))

        # LOAD CLASSIFIERS
        face_classifier = CascadeClassifier(haarcascades + 'haarcascade_frontalface_alt.xml')
        eye_classifier = CascadeClassifier(haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
        classifiers = (face_classifier, eye_classifier)
        print('{}>{} Classifiers loaded'.format(Fore.BLUE, Fore.RESET))

        # RETRIEVE CLEAR URLs FILE
        rules_file = open('{}/orders/utility/clear_rules.json'.format(wd))
        rules = load(rules_file)
        print('{}>{} Clear URLs file retrieved'.format(Fore.BLUE, Fore.RESET))

        # RETRIEVE KANJI LIST
        kanji_list_file = open('{}/orders/utility/kanji.json'.format(wd))
        kanji_list = load(kanji_list_file)
        print('{}>{} Kanji list file retrieved'.format(Fore.BLUE, Fore.RESET))

        # LOAD FONT PARAMS
        font = FONT_HERSHEY_SIMPLEX
        line_aa = LINE_AA
        font_params = (font, line_aa)
        print('{}>{} Font parameters loaded'.format(Fore.BLUE, Fore.RESET))

        # CREATE CONTEXT QUERIES LIST
        context_queries = list()
        print('{}>{} Context queries list created'.format(Fore.BLUE, Fore.RESET))

        # TELEGRAM BOT
        app = ApplicationBuilder().token(key).connection_pool_size(4).read_timeout(60).write_timeout(60).http_version("2").concurrent_updates(4).build()
        print('{}>{} Bot starting ...'.format(Fore.BLUE, Fore.RESET))

        app.add_handler(CommandHandler('start', help_command, block=False))
        app.add_handler(CommandHandler('help', help_command, block=False))
        app.add_handler(MessageHandler(filters.TEXT, msg_filter, block=False))
        app.add_handler(CallbackQueryHandler(btn, block=False))

        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(str(e))
