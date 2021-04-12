import sys
import secret

from order import Order
from telegram import Update, User
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

# Message sent when help is needed
def help_command( update: Update, _: CallbackContext ) -> None:
    update.message.reply_text( 'This is my command list: ' )

 # Message sent when the bot starts
def start( update: Update, _: CallbackContext ) -> None:
    update.message.reply_text( 'Hello!' )

# Checks if some command is written
def check_event( update: Update, _: CallbackContext ) -> None:
    try:
        msg = update._effective_message
        user = msg.from_user

        if not user.is_bot:
            order = Order( msg ).get_answer()
            type = order.get( 'type' )

            if type == 'audio':
                update.message.reply_audio(
                    audio=open( order.get( 'send' ), 'rb' ),
                    reply_to_message_id=order.get( 'msg_id' )
                )
            elif type == 'photo':
                update.message.reply_photo(
                    photo=open( order.get( 'send' ), 'rb' ),
                    reply_to_message_id=order.get( 'msg_id' )
                )
            elif type == 'text':
                update.message.reply_text(
                    order.get( 'send' ),
                    parse_mode=order.get( 'parse' ),
                    reply_to_message_id=order.get( 'msg_id' )
                )
    except Exception as e:
        print(e)

# Main bot function
def main() -> None:
    updater = Updater( secret.get_key( 'telegram' ) )
    dispatcher = updater.dispatcher

    dispatcher.add_handler( CommandHandler( 'help', help_command ) )
    dispatcher.add_handler( CommandHandler( 'start', start ) )

    dispatcher.add_handler( MessageHandler( Filters.text, check_event ) )

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()