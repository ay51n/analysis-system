import spacy
from pymongo import MongoClient, errors as mongo_errors
from datetime import datetime
import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

# Connect to MongoDB
def connect_to_mongo():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['project_chatbot']
        logging.info("Connected to MongoDB.")
        return db
    except mongo_errors.ConnectionFailure as e:
        logging.error("Could not connect to MongoDB: %s", e)
        raise

brands_mapping = {
    'apple': ['iphone', 'macbook', 'ipad', 'apple watch', 'imac'],
    'samsung': ['galaxy', 'note', 'samsung tv', 'samsung monitor'],
    'sony': ['playstation', 'sony camera', 'bravia', 'xperia'],
    'canon': ['eos', 'powershot', 'canon printer'],
    'nikon': ['coolpix', 'nikon dslr', 'nikkor lens'],
    'dell': ['xps', 'alienware', 'dell monitor', 'latitude'],
    'hp': ['envy', 'spectre', 'pavilion', 'hp printer'],
    'lenovo': ['thinkpad', 'yoga', 'lenovo legion', 'ideapad'],
    'lg': ['lg tv', 'lg refrigerator', 'lg washer', 'lg dryer'],
    'bose': ['bose headphones', 'bose speakers', 'bose soundbar'],
    'adidas': ['adidas shoes', 'adidas clothing', 'adidas accessories'],
    'nike': ['nike shoes', 'nike clothing', 'nike accessories'],
    'gucci': ['gucci bags', 'gucci clothing', 'gucci accessories'],
    'chanel': ['chanel perfume', 'chanel handbags', 'chanel clothing'],
    'toyota': ['toyota camry', 'toyota corolla', 'toyota rav4'],
    'honda': ['honda civic', 'honda accord', 'honda cr-v'],
    'audi': ['audi a4', 'audi q5', 'audi r8'],
    'mercedes': ['mercedes c-class', 'mercedes e-class', 'mercedes s-class'],
    'volkswagen': ['volkswagen golf', 'volkswagen passat', 'volkswagen atlas'],
    'fitbit': ['fitbit versa', 'fitbit charge', 'fitbit inspire'],
    'under armour': ['under armour shoes', 'under armour clothing', 'under armour accessories'],
    'patagonia': ['patagonia jacket', 'patagonia fleece', 'patagonia backpack'],
    'columbia': ['columbia jacket', 'columbia pants', 'columbia hiking boots'],
    'north face': ['north face jacket', 'north face backpack', 'north face gloves'],
    'asus': ['asus laptop', 'asus router', 'asus monitor'],
    'msi': ['msi gaming laptop', 'msi graphics card', 'msi motherboard'],
    'logitech': ['logitech mouse', 'logitech keyboard', 'logitech webcam'],
    'corsair': ['corsair ram', 'corsair power supply', 'corsair gaming headset'],
}


categories_mapping = {
    'Électronique': ['smartphone', 'phone', 'mobile', 'laptop', 'computer', 'camera', 'headphones', 'speaker', 'tablet'],
    'Loisirs': ['game', 'console', 'puzzle', 'card game', 'board game', 'sport equipment'],
    'Bien-être': ['fitness tracker', 'yoga mat', 'treadmill', 'dumbbell', 'gym membership'],
    'Cuisine': ['blender', 'microwave', 'cookbook', 'knife set', 'grill'],
    'Voyage': ['luggage', 'backpack', 'travel guide', 'plane ticket', 'travel pillow'],
    'Maison': ['furniture', 'bedding', 'tool kit', 'lighting', 'home decor'],
    'Financier': ['bank account', 'credit card', 'investment fund', 'stock market', 'cryptocurrency'],
    'Éducation': ['textbook', 'online course', 'study guide', 'educational app', 'stationery'],
    'Animaux de compagnie': ['pet food', 'leash', 'aquarium', 'pet toy', 'grooming service'],
    'Sport': ['football', 'basketball', 'tenni', 'soccer', 'baseball', 'volleyball', 'swimming', 'golf', 'cycling', 'running'],
    'Mode': ['clothing', 'shoe', 'accessorie', 'handbag', 'jewelry', 'watche','bag']
}


# Extract keywords 
def extract_keywords(text):
    doc = nlp(text)
    return [token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB', 'NUM']]

# Extract brands from the latest messages
def extract_brands_from_messages(messages):
    brands = set()
    for message in messages:
        text = message.get('text', '').lower()
        for brand in brands_mapping:
            if brand in text:
                brands.add(brand)
    return list(brands)

# Determine the category based on keywords
def find_category(keywords):
    for category, items_list in categories_mapping.items():
        if any(item in items_list for item in keywords):
            return category

# Determine the item types based on keywords
def find_items(keywords):
    items = set()
    for items_list in categories_mapping.values():
        items.update(set(keyword for keyword in keywords if keyword in items_list))
    return items

# Process each conversation to update or insert client data
def process_conversation(db, conversation):
    try:
        client_collection = db['client']
        user_events = [event for event in conversation.get('events', []) if event['event'] == 'user']
        
        if not user_events:
            return  # No user messages to process

        # Extract address from conversation or set it to an empty string
        address = conversation.get('address',[])

        # Initial processing based on the latest two user messages
        latest_messages = sorted(user_events, key=lambda x: x['timestamp'], reverse=True)[:2]
        combined_text = '/'.join(msg.get('text', '') for msg in latest_messages)
        latest_datetime = datetime.fromtimestamp(latest_messages[0]['timestamp'])
        keywords = extract_keywords(combined_text)

        # Attempt to determine category and items from the latest processed keywords
        category = find_category(keywords)
        items = find_items(keywords)

        if category == 'Unknown' or not items:
            for older_message in sorted(user_events, key=lambda x: x['timestamp'], reverse=True)[2:]:
                older_keywords = extract_keywords(older_message.get('text', ''))
                older_category = find_category(older_keywords)
                older_items = find_items(older_keywords)
                if older_category != 'Unknown' or older_items:
                    category = older_category if older_category != 'Unknown' else category
                    items = older_items if older_items else items
                    break

        brands_from_messages = extract_brands_from_messages(user_events)
        brands = list(set(brands_from_messages))  # Extract brands from the conversation

        # Update the database entry for the client
        processed_info = {
            'client_id': conversation['sender_id'],
            'category': category,
            'item': list(items),
            'brands': brands,  # Use brands extracted from messages
            'text': combined_text,
            'latest_message_date': latest_datetime,
            'address': address  # Include address in processed information
        }

        client_collection.update_one(
            {'client_id': processed_info['client_id']},
            {'$set': processed_info},
            upsert=True
        )
        logging.info(f"Processed and updated conversation for client_id {processed_info['client_id']}")
    except Exception as e:
        logging.error("Failed to process conversation: %s", e)

def process_all_conversations():
    db = connect_to_mongo()
    all_conversations = db['conversation'].find()
    for conversation in all_conversations:
        process_conversation(db, conversation)
    logging.info("Completed processing all conversations.")

# Define a function to continuously monitor for new conversations
def monitor_new_conversations(interval=60):
    while True:
        process_all_conversations()  # Process all conversations in the database
        time.sleep(interval)  # Wait for the specified interval before checking again

if __name__ == "__main__":
    monitor_new_conversations()
