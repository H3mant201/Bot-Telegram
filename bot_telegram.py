from pymongo import MongoClient
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# Conexión a MongoDB
client = MongoClient('mongodb+srv://hmansukhani:LEepwe6RN6ujSQe9@cluster0.8uyvf.mongodb.net/')
db = client['supermercat']
productes_coll = db['productes']

# Carrito de compra (almacenado en memoria)
carro = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Missatge de benvinguda."""
    await update.message.reply_text(
        "👋 Hola! Benvingut al bot del supermercat.\n"
        "Utilitza /help per a veure els comandos disponibles."
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Llista els comandos disponibles."""
    await update.message.reply_text(
        "Comandes disponibles:\n"
        "/info <codi_producte> - Informació d'un producte.\n"
        "/imatge <codi_producte> - Imatge d'un producte.\n"
        "/add <codi_producte> <quantitat> - Afegir productes al carret.\n"
        "/carro - Veure el contingut del carret."
    )

async def info_producte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retorna informació bàsica d'un producte."""
    if len(context.args) != 1:
        await update.message.reply_text("Utilitza: /info <codi_producte>")
        return


    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte:
        mensaje = (
            f"**Nom:** {producte['nom']}\n"
            f"**Preu:** {producte.get('preu', 'No disponible')}€\n"
            f"**Categoria:** {producte['id_category']}"
        )
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        await update.message.reply_text("Producte no trobat.")

async def imatge_producte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia la imatge d'un producte des de la seva URL."""
    if len(context.args) != 1:
        await update.message.reply_text("Utilitza: /imatge <codi_producte>")
        return

    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte and 'imatge' in producte:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=producte['imatge'])
    else:
        await update.message.reply_text("Imatge no disponible per a aquest producte.")

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Afegeix un producte al carret de compres."""
    if len(context.args) != 2:
        await update.message.reply_text("Utilitza: /add <codi_producte> <quantitat>")
        return

    codi_producte = context.args[0]
    try:
        quantitat = int(context.args[1])
    except ValueError:
        await update.message.reply_text("La quantitat ha de ser un número.")
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
        await update.message.reply_text(f"{quantitat} unitat(s) de {producte['nom']} afegides al carret.")
    else:
        await update.message.reply_text("Producte no trobat.")

async def veure_carro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra el contingut del carret."""
    if not carro:
        await update.message.reply_text("El carret està buit." if update.message else "El carret està buit.")
        return

    mensaje = "🛒 Carret de compres:\n"
    total = 0
    for codi, info in carro.items():
        # Convertir 'preu' a float y 'quantitat' a int antes de la operación
        try:
            preu = float(info['preu'])
            quantitat = int(info['quantitat'])
            subtotal = preu * quantitat
        except ValueError:
            await update.message.reply_text("Error en los datos del carrito." if update.message else "Error en los datos del carrito.")
            return
        
        total += subtotal
        mensaje += f"- {info['nom']}: {quantitat} x {preu}€ = {subtotal:.2f}€\n"
    
    mensaje += f"\n**Total:** {total:.2f}€"
    
    if update.message:
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        # Si 'update.message' es None, manejamos la situación
        print("Error: No se pudo enviar el mensaje porque 'update.message' es None.")



def main():
    # Token del bot
    TOKEN = open('./token.txt').read().strip()

    # Crear l'aplicació
    application = Application.builder().token(TOKEN).build()

    # Afegir les comandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("info", info_producte))
    application.add_handler(CommandHandler("imatge", imatge_producte))
    application.add_handler(CommandHandler("add", add_to_cart))
    application.add_handler(CommandHandler("carro", veure_carro))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
