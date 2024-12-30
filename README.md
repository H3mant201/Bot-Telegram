# Bot Mercadona

Aquest bot permet interactuar amb productes emmagatzemats a la meva base de dades MongoDB utilitzant la API de Telegram. Les funcionalitats inclouen consultar informació de productes, obtenir imatges i gestionar un carret de compra.

## Requisits

- **Python**: Assegura't de tenir Python instal·lat.
- **Dependències**: Instal·la les següents dependències:
  ```bash
  pip install python-telegram-bot
  pip install pymongo
  ```
- **MongoDB**: Utilitzarem la base de dades creada anterirment amb una col·lecció `productes` que contingui els productes amb els camps: `aneu`, `nom`, `preu`, `aneu_category`, i `imatge` (URL de la imatge).
- **Token del bot**: Necesitarem el Token del nostre bot per poder-hi accedir.

---

## Codi del Bot

### Importacions i Configuració Inicial

```python
from pymongo import MongoClient
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# Connexió a MongoDB
client = MongoClient('mongodb+srv://usuario:password@cluster.mongodb.net/')
db = client['supermercat']
productes_coll = db['productes']

# Carret de compra (emmagatzemat en memòria)
carro = {}
```

### Funcions de Comandes

#### `/start`

Envia un missatge de benvinguda a l'usuari.

```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Missatge de benvinguda."""
    await update.message.reply_text(
        "Hola! Benvingut al bot del supermercat.\n"
        "Utilitza /help per a veure els comandos disponibles."
    )
```

#### `/help`

Llista els comandos disponibles per a l'usuari.

```python
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Llista els comandos disponibles."""
    await update.message.reply_text(
        "Comandes disponibles:\n"
        "/info <codi_producte> - Informació d'un producte.\n"
        "/imatge <codi_producte> - Imatge d'un producte.\n"
        "/add <codi_producte> <quantitat> - Afegir productes al carret.\n"
        "/carro - Veure el contingut del carret."
    )
```

#### `/info <codi_producte>`

Retorna informació bàsica d'un producte.

```python
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
```

#### `/imatge <codi_producte>`

Envia la imatge d'un producte des de la seva URL.

```python
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
```

#### `/add <codi_producte> <quantitat>`

Afegeix un producte al carret de compres.

```python
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
```

#### `/carret`

Mostra el contingut del carret.

```python
async def veure_carro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra el contingut del carret."""
    if not carro:
        await update.message.reply_text("El carret està buit." if update.message else "El carret està buit.")
        return

    mensaje = "Carret de compres:\n"
    total = 0
    for codi, info in carro.items():
        # Convertir 'preu' a float i 'quantitat' a int 
        try:
            preu = float(info['preu'])
            quantitat = int(info['quantitat'])
            subtotal = preu * quantitat
        except ValueError:
            await update.message.reply_text("Error en les dades del carro." if update.message else "Error en les dades del carro.")
            return
        
        total += subtotal
        mensaje += f"- {info['nom']}: {quantitat} x {preu}€ = {subtotal:.2f}€\n"
    
    mensaje += f"\n**Total:** {total:.2f}€"
    
    if update.message:
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        print("Error: No s'ha pogut enviar el missatge perque 'update.message' es None.")
```

### Configuració Principal

```python
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
    application.add_handler(CommandHandler("carret", veure_carro))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
```