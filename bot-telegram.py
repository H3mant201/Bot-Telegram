from pymongo import MongoClient
from telegram import Update, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler

# Conexión a MongoDB
client = MongoClient('mongodb+srv://hmansukhani:LEepwe6RN6ujSQe9@cluster0.8uyvf.mongodb.net/')
db = client['supermercat']
productes_coll = db['productes']

# Carro de compra (almacenado temporalmente en memoria)
carro = {}

def start(update: Update, context: CallbackContext) -> None:
    """
    Mensaje de bienvenida al bot.
    """
    update.message.reply_text(
        "Hola! Sóc el bot del supermercat.\n"
        "Pots usar les següents comandes:\n"
        "/info <codi_producte> - Obtenir informació d'un producte.\n"
        "/imatge <codi_producte> - Veure la imatge d'un producte.\n"
        "/add <codi_producte> <quantitat> - Afegir productes al carro.\n"
        "/carro - Veure el teu carro de compra."
    )

def info_producte(update: Update, context: CallbackContext) -> None:
    """
    Retorna informació bàsica d'un producte a partir del seu codi.
    """
    if len(context.args) != 1:
        update.message.reply_text("Usa: /info <codi_producte>")
        return

    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte:
        missatge = (
            f"**Nom:** {producte['nom']}\n"
            f"**Preu:** {producte.get('preu', 'No disponible')}€\n"
            f"**Categoria:** {producte['id_category']}"
        )
        update.message.reply_text(missatge, parse_mode='Markdown')
    else:
        update.message.reply_text("Producte no trobat.")

def imatge_producte(update: Update, context: CallbackContext) -> None:
    """
    Envia la imatge d'un producte a partir del seu codi.
    """
    if len(context.args) != 1:
        update.message.reply_text("Usa: /imatge <codi_producte>")
        return

    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte and 'imatge' in producte:
        update.message.reply_photo(producte['imatge'])
    else:
        update.message.reply_text("Imatge no trobada per aquest producte.")

def add_to_cart(update: Update, context: CallbackContext) -> None:
    """
    Afegeix productes al carro de compra.
    """
    if len(context.args) != 2:
        update.message.reply_text("Usa: /add <codi_producte> <quantitat>")
        return

    codi_producte = context.args[0]
    try:
        quantitat = int(context.args[1])
    except ValueError:
        update.message.reply_text("La quantitat ha de ser un número.")
        return

    producte = productes_coll.find_one({"id": codi_producte})

    if producte:
        if codi_producte in carro:
            carro[codi_producte]['quantitat'] += quantitat
        else:
            carro[codi_producte] = {
                'nom': producte['nom'],
                'preu': producte.get('preu', 0),
                'quantitat': quantitat
            }
        update.message.reply_text(f"{quantitat} unitats de {producte['nom']} afegides al carro.")
    else:
        update.message.reply_text("Producte no trobat.")

def veure_carro(update: Update, context: CallbackContext) -> None:
    """
    Mostra el contingut del carro de compra.
    """
    if not carro:
        update.message.reply_text("El teu carro està buit.")
        return

    missatge = "El teu carro de compra:\n"
    total = 0
    for codi, info in carro.items():
        subtotal = info['preu'] * info['quantitat']
        total += subtotal
        missatge += f"- {info['nom']}: {info['quantitat']} unitats x {info['preu']}€ = {subtotal:.2f}€\n"
    missatge += f"\n**Total:** {total:.2f}€"
    update.message.reply_text(missatge, parse_mode='Markdown')

def main():
    """
    Configura i inicia el bot.
    """
    TOKEN = open('./token.txt').read().strip()
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Comandes del bot
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("info", info_producte))
    dispatcher.add_handler(CommandHandler("imatge", imatge_producte))
    dispatcher.add_handler(CommandHandler("add", add_to_cart))
    dispatcher.add_handler(CommandHandler("carro", veure_carro))

    # Inicia el bot
    updater.start_polling()
    

if __name__ == "__main__":
    main()

