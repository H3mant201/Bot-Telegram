# Bot Mercadona

Aquest bot permet interactuar amb productes emmagatzemats en una base de dades MongoDB utilitzant la API de Telegram. Les funcionalitats inclouen consultar informació de productes, obtenir imatges i gestionar un carret de compra.

## Requisitos previos

- **Python**: Asegúrate de tener Python instalado.
- **Dependencias**: Instala las siguientes dependencias:
  ```bash
  pip install python-telegram-bot pymongo
  ```
- **MongoDB**: Configura una base de datos con una colección `productes` que contenga los productos con los campos: `id`, `nom`, `preu`, `id_category`, e `imatge` (URL de la imagen).
- **Token del bot**: Incluye un archivo `token.txt` en el directorio raíz con el token de tu bot de Telegram.

---

## Código del Bot

### Importaciones y Configuración Inicial

```python
from pymongo import MongoClient
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# Conexión a MongoDB
client = MongoClient('mongodb+srv://usuario:password@cluster.mongodb.net/')
db = client['supermercat']
productes_coll = db['productes']

# Carrito de compra (almacenado en memoria)
carro = {}
```

### Funciones de Comandos

#### `/start`

Envía un mensaje de bienvenida al usuario.

```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mensaje de bienvenida."""
    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al bot del supermercado.\n"
        "Usa /help para ver los comandos disponibles."
    )
```

#### `/help`

Lista los comandos disponibles para el usuario.

```python
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista los comandos disponibles."""
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/info <codi_producte> - Información de un producto.\n"
        "/imatge <codi_producte> - Imagen de un producto.\n"
        "/add <codi_producte> <quantitat> - Añadir productos al carrito.\n"
        "/carro - Ver el contenido del carrito."
    )
```

#### `/info <codi_producte>`

Devuelve información básica de un producto.

```python
async def info_producte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Devuelve información básica de un producto."""
    if len(context.args) != 1:
        await update.message.reply_text("Usa: /info <codi_producte>")
        return

    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte:
        mensaje = (
            f"**Nombre:** {producte['nom']}\n"
            f"**Precio:** {producte.get('preu', 'No disponible')}€\n"
            f"**Categoría:** {producte['id_category']}"
        )
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        await update.message.reply_text("Producto no encontrado.")
```

#### `/imatge <codi_producte>`

Envía la imagen de un producto desde su URL.

```python
async def imatge_producte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía la imagen de un producto desde su URL."""
    if len(context.args) != 1:
        await update.message.reply_text("Usa: /imatge <codi_producte>")
        return

    codi_producte = context.args[0]
    producte = productes_coll.find_one({"id": codi_producte})

    if producte and 'imatge' in producte:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=producte['imatge'])
    else:
        await update.message.reply_text("Imagen no disponible para este producto.")
```

#### `/add <codi_producte> <quantitat>`

Añade un producto al carrito de compras.

```python
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Añade un producto al carrito."""
    if len(context.args) != 2:
        await update.message.reply_text("Usa: /add <codi_producte> <quantitat>")
        return

    codi_producte = context.args[0]
    try:
        quantitat = int(context.args[1])
    except ValueError:
        await update.message.reply_text("La cantidad debe ser un número.")
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
        await update.message.reply_text(f"{quantitat} unidad(es) de {producte['nom']} añadidas al carrito.")
    else:
        await update.message.reply_text("Producto no encontrado.")
```

#### `/carro`

Muestra el contenido del carrito.

```python
async def veure_carro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el contenido del carrito."""
    if not carro:
        await update.message.reply_text("El carrito está vacío.")
        return

    mensaje = "🛒 Carrito de compra:\n"
    total = 0
    for codi, info in carro.items():
        subtotal = info['preu'] * info['quantitat']
        total += subtotal
        mensaje += f"- {info['nom']}: {info['quantitat']} x {info['preu']}€ = {subtotal:.2f}€\n"
    mensaje += f"\n**Total:** {total:.2f}€"
    await update.message.reply_text(mensaje, parse_mode='Markdown')
```

### Configuración Principal

```python
def main():
    # Token del bot
    TOKEN = open('./token.txt').read().strip()

    # Crear la aplicación
    application = Application.builder().token(TOKEN).build()

    # Añadir los comandos
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
```