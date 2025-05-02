from werkzeug.security import generate_password_hash
import csv
import random
from faker import Faker
import datetime
from decimal import Decimal, ROUND_HALF_UP

# Configuration
num_users = 1000  # replace 500 to 1000 in order to make it as same as num_accounts --jiechen
num_sellers = 200
num_accounts = 1000
num_categories = 50
num_products = 2000
num_purchases = 1000
num_purchase_items = 3000
num_seller_purchases = 1500
num_seller_purchase_items = 4000
num_product_reviews = 800
num_seller_reviews = 500
num_cart = 900
num_cart_items = 700
num_inventory_items = 3000
num_account_transactions = 1500

# Initialize Faker
Faker.seed(0)
fake = Faker()

def sanitize_text(text):
    """Remove commas from text to avoid CSV parsing issues"""
    if text is None:
        return ""
    return str(text).replace(',', ' - ')

def get_csv_writer(f):
    return csv.writer(f, dialect='unix', quoting=csv.QUOTE_MINIMAL)

def round_decimal(amount):
    """Round decimal to 2 places"""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return str(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def gen_users(num_users):
    """Generate Users table"""
    with open('Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for user_id in range(1, num_users + 1):
            if user_id % 50 == 0:
                print(f'{user_id}', end=' ', flush=True)
            writer.writerow([user_id])
        print(f'{num_users} generated')
    return list(range(1, num_users + 1))

def gen_sellers(num_sellers):
    """Generate Sellers table"""
    with open('Sellers.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Sellers...', end=' ', flush=True)
        for seller_id in range(1, num_sellers + 1):
            if seller_id % 20 == 0:
                print(f'{seller_id}', end=' ', flush=True)
            name = fake.company()
            address = fake.address().replace('\n', ', ')
            writer.writerow([
                seller_id,
                name,
                address
            ])
        print(f'{num_sellers} generated')
    return list(range(1, num_sellers + 1))

# def gen_accounts(num_accounts, user_ids, seller_ids):
#     """Generate Accounts table"""
#     used_emails = set()
#     with open('Accounts.csv', 'w') as f:
#         writer = get_csv_writer(f)
#         print('Accounts...', end=' ', flush=True)
#         for account_id in range(1, num_accounts + 1):
#             if account_id % 100 == 0:
#                 print(f'{account_id}', end=' ', flush=True)
            
#             # Ensure unique email
#             while True:
#                 profile = fake.profile()
#                 email = profile['mail']
#                 if email not in used_emails:
#                     used_emails.add(email)
#                     break
            
#             user_id = random.choice(user_ids)
#             # Only 30% of accounts are seller accounts
#             seller_id = random.choice(seller_ids) if random.random() < 0.3 else None
#             plain_password = f'pass{account_id}'
#             password = generate_password_hash(plain_password)
#             name = profile['name']
#             address = fake.address().replace('\n', ', ')
#             balance = round_decimal(str(random.uniform(0, 10000)))
            
#             writer.writerow([
#                 account_id,
#                 user_id,
#                 seller_id if seller_id is not None else '',
#                 email,
#                 password,
#                 name,
#                 address,
#                 balance
#             ])
#         print(f'{num_accounts} generated')
#     return list(range(1, num_accounts + 1))

# /////////////////////////////generate account.csv to make user_id unique ---jiechen//////////////////////////////////////////////////////
def gen_accounts(num_accounts, user_ids, seller_ids):
    """Generate Accounts table with unique user_id"""
    used_emails = set()

    # Ensure num_accounts ≤ num_users
    assert num_accounts <= len(user_ids), "num_accounts exceeds number of users!"

    selected_user_ids = random.sample(user_ids, num_accounts)  # Unique user_ids only

    with open('Accounts.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Accounts...', end=' ', flush=True)

        for idx, user_id in enumerate(selected_user_ids, start=1):
            if idx % 100 == 0:
                print(f'{idx}', end=' ', flush=True)

            # Unique email generation
            while True:
                profile = fake.profile()
                email = profile['mail']
                if email not in used_emails:
                    used_emails.add(email)
                    break
            seller_id = random.choice(seller_ids) if random.random() < 0.3 else None
            plain_password = f'pass{idx}'
            password = generate_password_hash(plain_password)
            name = profile['name']
            address = fake.address().replace('\n', ', ')
            balance = round_decimal(str(random.uniform(0, 10000)))

            writer.writerow([
                idx,  # account_id
                user_id,
                seller_id if seller_id else '',
                email,
                password,
                name,
                address,
                balance
            ])
        print(f'{num_accounts} generated')

    return list(range(1, num_accounts + 1))
# ////////////////////////////////gen_end ---jiechen/////////////////////////////////////////////////////////////////////////////

def gen_categories(num_categories):
    """Generate Categories table with realistic category names"""
    # Define main categories
    main_category_names = [
        "Electronics", "Clothing", "Home & Kitchen", "Beauty & Personal Care",
        "Sports & Outdoors", "Books", "Toys & Games", "Automotive",
        "Health & Wellness", "Jewelry"
    ]
    
    # Define subcategories for each main category
    subcategories = {
        "Electronics": [
            "Smartphones", "Laptops", "Audio", "Cameras", "Wearable Tech",
            "Tablets", "Monitors", "Computer Accessories", "Smart Home", "TV & Video"
        ],
        "Clothing": [
            "Men's Apparel", "Women's Fashion", "Kids' Clothing", "Shoes",
            "Activewear", "Accessories", "Outerwear", "Underwear", "Formal Wear", "Seasonal"
        ],
        "Home & Kitchen": [
            "Cookware", "Bedding", "Bath", "Home Decor", "Storage & Organization",
            "Cleaning Supplies", "Dining", "Kitchen Appliances", "Lighting", "Furniture"
        ],
        "Beauty & Personal Care": [
            "Skincare", "Makeup", "Hair Care", "Fragrances", "Bath & Body",
            "Men's Grooming", "Oral Care", "Sun Care", "Beauty Tools", "Natural Beauty"
        ],
        "Sports & Outdoors": [
            "Exercise Equipment", "Outdoor Recreation", "Team Sports", "Water Sports",
            "Camping", "Hiking", "Cycling", "Winter Sports", "Fitness Accessories", "Athletic Clothing"
        ],
        "Books": [
            "Fiction", "Non-Fiction", "Children's Books", "Textbooks", "Self-Help",
            "Cookbooks", "Biographies", "History", "Science Fiction", "Romance"
        ],
        "Toys & Games": [
            "Board Games", "Action Figures", "Dolls", "Educational Toys", "Puzzles",
            "Outdoor Toys", "Arts & Crafts", "Building Toys", "Electronic Toys", "Stuffed Animals"
        ],
        "Automotive": [
            "Car Accessories", "Maintenance", "Tools", "Interior", "Exterior",
            "Electronics", "Tires & Wheels", "Motorcycle", "Oils & Fluids", "Safety"
        ],
        "Health & Wellness": [
            "Vitamins & Supplements", "Fitness Nutrition", "Medical Supplies", "Personal Care",
            "Wellness Equipment", "Sleep Aids", "First Aid", "Massage", "Aromatherapy", "Weight Management"
        ],
        "Jewelry": [
            "Rings", "Necklaces", "Earrings", "Bracelets", "Watches",
            "Men's Jewelry", "Fine Jewelry", "Fashion Jewelry", "Wedding & Engagement", "Jewelry Boxes"
        ]
    }
    
    # Define descriptions for each category type
    descriptions = {
        "Electronics": "Discover the latest technology and gadgets for work and entertainment.",
        "Clothing": "Find stylish and comfortable clothing for every occasion and season.",
        "Home & Kitchen": "Everything you need to make your house a home, from essentials to decor.",
        "Beauty & Personal Care": "Top-quality beauty products and personal care essentials.",
        "Sports & Outdoors": "Gear and equipment for all your favorite sports and outdoor activities.",
        "Books": "Explore our vast collection of books across all genres and interests.",
        "Toys & Games": "Fun and educational toys and games for all ages.",
        "Automotive": "Keep your vehicle running smoothly with our automotive products.",
        "Health & Wellness": "Products to help you maintain a healthy lifestyle and well-being.",
        "Jewelry": "Beautiful jewelry pieces to complement any style or occasion."
    }
    
    # Create a mapping to track which category ID corresponds to which category name
    category_mapping = {}
    
    # Determine how many main categories to use based on the requested total
    num_main_categories = min(len(main_category_names), max(3, int(num_categories * 0.2)))
    selected_main_categories = main_category_names[:num_main_categories]
    
    with open('Categories.csv', 'w', newline='', encoding='utf-8') as f:
        writer = get_csv_writer(f)
        print('Categories...', end=' ', flush=True)
        
        # Create main categories first
        category_id = 1
        for main_category in selected_main_categories:
            description = descriptions.get(main_category, fake.sentence(nb_words=10))
            parent_id = None  # No parent for main categories
            writer.writerow([
                category_id,
                main_category,
                description,
                parent_id if parent_id is not None else '',
            ])
            category_mapping[category_id] = main_category
            category_id += 1
        
        # Create subcategories
        main_category_ids = list(range(1, num_main_categories + 1))
        
        while category_id <= num_categories:
            if category_id % 10 == 0:
                print(f'{category_id}', end=' ', flush=True)
            
            # Choose a random main category to create a subcategory for
            parent_id = random.choice(main_category_ids)
            parent_category = category_mapping[parent_id]
            
            # Get the subcategories list for this main category
            sub_list = subcategories.get(parent_category, [])
            
            if sub_list and len(sub_list) > 0:
                # Use a predefined subcategory if available
                sub_index = (category_id - num_main_categories - 1) % len(sub_list)
                name = sub_list[sub_index]
                description = f"Products in our {name} collection within {parent_category}."
            else:
                # Generate a random subcategory if we've run out of predefined ones
                name = fake.unique.word().capitalize() + " " + fake.word()
                description = fake.sentence(nb_words=10)
            
            writer.writerow([
                category_id,
                name,
                description,
                parent_id
            ])
            
            category_mapping[category_id] = name
            category_id += 1
            
        print(f'{num_categories} generated')
    
    # Return both the category IDs and the mapping dictionary
    return list(range(1, num_categories + 1)), category_mapping

fake = Faker()


def generate_product_description(product_name, category_name):
    """Generate a realistic product description based on the product name and category"""
    
    # Extract key elements from the product name
    elements = product_name.lower().split()
    brand = elements[0] if elements else "Brand"
    
    # Base descriptions for different product types
    electronics_desc = {
        "smartphone": "Experience the latest technology with this {brand} smartphone. Featuring a stunning display, powerful processor, and exceptional camera system. Perfect for staying connected, capturing memories, and enjoying your favorite content on the go.",
        "laptop": "Elevate your productivity with this {brand} laptop. Designed for performance with a fast processor, ample storage, and crisp display. Ideal for work, entertainment, and creativity wherever you go.",
        "headphones": "Immerse yourself in rich, clear sound with these {brand} headphones. Featuring comfortable ear cushions and excellent noise isolation. Perfect for music, calls, and entertainment.",
        "tv": "Transform your living room with this {brand} TV. Enjoy stunning picture quality, vibrant colors, and smart features for all your entertainment needs. Stream your favorite content with ease.",
        "tablet": "Stay productive and entertained with this versatile {brand} tablet. Featuring a responsive touchscreen, powerful performance, and long battery life. Perfect for browsing, reading, and media consumption.",
        "camera": "Capture life's precious moments with exceptional clarity using this {brand} camera. With advanced features and intuitive controls, it's perfect for both beginners and photography enthusiasts.",
        "console": "Dive into immersive gaming experiences with this {brand} gaming console. Featuring powerful graphics, fast loading times, and access to an extensive library of games for endless entertainment.",
        "monitor": "Enhance your viewing experience with this {brand} monitor. Featuring crisp visuals, accurate colors, and eye-comfort technology for reduced strain during long usage sessions.",
        "speaker": "Fill your space with rich, room-filling sound from this {brand} speaker. With clear highs and deep bass, it delivers an immersive audio experience for music, movies, and more.",
        "smartwatch": "Track your fitness goals and stay connected with this feature-packed {brand} smartwatch. With health monitoring, notifications, and long battery life, it's your perfect daily companion.",
        "drone": "Explore the world from above with this {brand} drone. Capture stunning aerial footage with its high-quality camera and enjoy precise control with its intuitive flight features.",
        "power bank": "Never run out of battery again with this reliable {brand} power bank. Compact yet powerful, it provides multiple charges for your devices when you're on the go."
    }
    
    clothing_desc = {
        "t-shirt": "Add a touch of style to your casual wardrobe with this comfortable {brand} t-shirt. Made from soft, breathable fabric that feels great against your skin. Perfect for everyday wear.",
        "jeans": "These premium {brand} jeans combine style and comfort for your everyday look. Featuring quality denim and expert craftsmanship for a perfect fit that lasts through countless wears.",
        "sneakers": "Step out in style with these {brand} sneakers. Designed for both comfort and fashion, they feature cushioned insoles and durable construction for all-day wear.",
        "dress": "Make a statement with this beautiful {brand} dress. The flattering silhouette and quality fabric ensure you'll look and feel amazing for any special occasion.",
        "jacket": "Stay warm and stylish with this versatile {brand} jacket. Perfect for layering in changing weather, it combines fashion and function for your everyday outfits.",
        "hoodie": "Stay cozy in this comfortable {brand} hoodie. Perfect for relaxed weekends or active days, it's made from soft fabric that keeps you warm without weighing you down.",
        "scarf": "Add a touch of elegance to any outfit with this beautiful {brand} scarf. The soft fabric and stylish design make it a versatile accessory for any season.",
        "cap": "Top off your casual look with this stylish {brand} cap. Featuring adjustable sizing for a perfect fit and quality construction for lasting wear.",
        "pants": "These versatile {brand} pants are a wardrobe essential. Combining comfort and style, they transition seamlessly from work to weekend activities.",
        "socks": "Keep your feet comfortable all day with these quality {brand} socks. Designed with cushioning in all the right places and made from breathable materials.",
        "coat": "Stay protected from the elements in style with this premium {brand} coat. The quality materials and expert tailoring ensure warmth and comfort in cold weather.",
        "skirt": "Add versatility to your wardrobe with this stylish {brand} skirt. The flattering cut and quality fabric make it perfect for both casual and dressier occasions."
    }
    
    home_desc = {
        "pan": "Elevate your cooking with this premium {brand} non-stick pan. Designed for even heat distribution and easy food release, it makes preparing your favorite dishes a pleasure.",
        "sheet": "Experience better sleep with these luxurious {brand} bed sheets. Made from high-quality materials for breathable comfort that lasts wash after wash.",
        "lamp": "Add ambient lighting to any room with this stylish {brand} table lamp. The elegant design complements your decor while providing perfect illumination for reading and relaxing.",
        "rug": "Transform your space with this beautiful {brand} rug. The quality materials and expert craftsmanship add comfort underfoot and a touch of style to any room.",
        "towel": "Wrap yourself in luxury with these premium {brand} towels. Absorbent and soft, they're the perfect addition to your bathroom for everyday comfort.",
        "pillow": "Rest your head on the perfect blend of support and comfort with this {brand} pillow. Designed for a restful night's sleep in any sleeping position.",
        "utensil": "Make meal preparation a pleasure with this quality {brand} utensil set. Featuring ergonomic handles and durable construction for years of cooking enjoyment.",
        "blanket": "Stay cozy year-round with this soft {brand} blanket. Perfect for snuggling on the couch or adding an extra layer of warmth to your bed.",
        "planter": "Display your favorite plants in style with this attractive {brand} planter. The quality materials and thoughtful design make it a beautiful addition to any space.",
        "curtains": "Control light and add privacy with these elegant {brand} curtains. The quality fabric and careful construction enhance your room's decor while serving a practical purpose.",
        "clock": "Keep track of time in style with this {brand} wall clock. The clean design and reliable mechanism make it both a functional timepiece and attractive decor element.",
        "organizer": "Bring order to any space with this practical {brand} organizer. Thoughtfully designed compartments help you store and access your items with ease."
    }
    
    beauty_desc = {
        "perfume": "Discover your signature scent with this exquisite {brand} perfume. The carefully crafted fragrance notes evolve throughout the day for a truly personal experience.",
        "cream": "Nourish your skin with this luxurious {brand} moisturizing cream. Formulated with quality ingredients to hydrate and protect your skin for a radiant complexion.",
        "makeup": "Express yourself with this premium {brand} makeup set. Featuring highly pigmented colors and long-lasting formulas for a flawless look that stays all day.",
        "shampoo": "Revitalize your hair with this specialized {brand} shampoo. Formulated to cleanse gently while addressing your specific hair needs for healthier-looking results.",
        "mascara": "Define and enhance your lashes with this {brand} mascara. The innovative formula adds volume and length without clumping for beautifully dramatic eyes.",
        "oil": "Enhance your wellbeing with this pure {brand} essential oil. The carefully extracted aroma creates a pleasant environment for relaxation and focus.",
        "polish": "Add a pop of color to your nails with this {brand} nail polish. The smooth application and chip-resistant formula keep your manicure looking fresh for days.",
        "foundation": "Achieve a flawless complexion with this {brand} foundation. The buildable coverage blends seamlessly for a natural-looking finish that lasts all day.",
        "kit": "Complete your skincare routine with this comprehensive {brand} skincare kit. Each product works together to cleanse, treat, and protect your skin for optimal results.",
        "lipstick": "Make a statement with this vibrant {brand} lipstick. The creamy formula glides on smoothly for comfortable wear and stunning color that lasts.",
        "deodorant": "Stay fresh and confident all day with this effective {brand} deodorant. The gentle formula provides long-lasting protection without irritating sensitive skin.",
        "serum": "Transform your skin with this powerful {brand} facial serum. Concentrated active ingredients target specific concerns for visible improvement in your complexion."
    }
    
    sports_desc = {
        "yoga": "Enhance your practice with this premium {brand} yoga mat. The perfect thickness provides cushioning for your joints while maintaining stability for all poses.",
        "bike": "Take your fitness to the next level with this {brand} exercise bike. The adjustable resistance and comfortable design make it perfect for home workouts of any intensity.",
        "dumbbell": "Build strength effectively with this quality {brand} dumbbell set. The comfortable grip and durable construction make them perfect for a variety of exercises.",
        "shoes": "Optimize your performance with these specialized {brand} running shoes. Designed with support and cushioning in all the right places for comfortable, injury-free training.",
        "racket": "Improve your game with this professional-grade {brand} tennis racket. The balanced design and quality strings give you better control and power on every shot.",
        "tent": "Make outdoor adventures more comfortable with this reliable {brand} camping tent. Quick to set up and designed to withstand the elements for worry-free camping.",
        "backpack": "Carry your gear in comfort with this thoughtfully designed {brand} backpack. Multiple compartments and ergonomic straps make it perfect for any activity.",
        "helmet": "Protect yourself in style with this safety-certified {brand} bicycle helmet. The adjustable fit and ventilation system ensure comfort during your rides.",
        "goggles": "Enhance your swimming experience with these comfortable {brand} goggles. The watertight seal and anti-fog lenses provide clear vision lap after lap.",
        "basketball": "Take your game to the court with this quality {brand} basketball. The perfect grip and bounce consistency improve your handling and shooting accuracy.",
        "poles": "Navigate any terrain with confidence using these sturdy {brand} trekking poles. Adjustable height and comfortable grips reduce strain on your joints during hikes.",
        "golf": "Improve your performance on the course with this premium {brand} golf set. Clubs for every situation help you tackle any hole with confidence."
    }
    
    # Default description if no specific one is found
    default_desc = "High-quality {brand} product designed to meet your needs. Featuring superior craftsmanship and materials, this item offers great value and performance. Add it to your cart today!"
    
    # Determine product type
    product_type = None
    description = None
    
    # Check for electronics
    if "Electronics" in category_name or any(word in category_name for word in ["Smartphones", "Laptops", "Audio", "TV", "Cameras"]):
        for key in electronics_desc:
            if key in product_name.lower():
                product_type = key
                description = electronics_desc[key].format(brand=brand)
                break
    
    # Check for clothing
    elif "Clothing" in category_name or any(word in category_name for word in ["Apparel", "Fashion", "Shoes", "Wear"]):
        for key in clothing_desc:
            if key in product_name.lower():
                product_type = key
                description = clothing_desc[key].format(brand=brand)
                break
    
    # Check for home
    elif "Home" in category_name or "Kitchen" in category_name or any(word in category_name for word in ["Cookware", "Bedding", "Bath", "Decor"]):
        for key in home_desc:
            if key in product_name.lower():
                product_type = key
                description = home_desc[key].format(brand=brand)
                break
    
    # Check for beauty
    elif "Beauty" in category_name or "Personal Care" in category_name or any(word in category_name for word in ["Skincare", "Makeup", "Hair", "Fragrances"]):
        for key in beauty_desc:
            if key in product_name.lower():
                product_type = key
                description = beauty_desc[key].format(brand=brand)
                break
    
    # Check for sports
    elif "Sports" in category_name or "Outdoors" in category_name or any(word in category_name for word in ["Exercise", "Fitness", "Camping", "Hiking"]):
        for key in sports_desc:
            if key in product_name.lower():
                product_type = key
                description = sports_desc[key].format(brand=brand)
                break
    
    # If no specific description was found, use a generic one based on product name keywords
    if description is None:
        # Try to find any key from any category
        all_desc = {**electronics_desc, **clothing_desc, **home_desc, **beauty_desc, **sports_desc}
        for key in all_desc:
            if key in product_name.lower():
                description = all_desc[key].format(brand=brand)
                break
        
        # If still no match, use default with some customization
        if description is None:
            # Extract potential product type from name (last word might be the product type)
            potential_type = elements[-1] if len(elements) > 1 else "product"
            description = default_desc.format(brand=brand).replace("product", potential_type)
    
    return description


# Modify the gen_products function to use the description generator and properly relate images to categories
def gen_products(num_products, category_ids, category_mapping, seller_ids, main_category_names=None):
    """Generate Products table with realistic product names based on categories"""
    # Define main category names if not provided
    if main_category_names is None:
        main_category_names = [
            "Electronics", "Clothing", "Home & Kitchen", "Beauty & Personal Care",
            "Sports & Outdoors", "Books", "Toys & Games", "Automotive",
            "Health & Wellness", "Jewelry"
        ]
    
    products = []
    used_names = set()
    
    # Define electronics templates and brands
    electronics_templates = [
        "Smartphone {brand} {series}", "Laptop {brand} {series} {size}\"", 
        "Bluetooth Headphones {brand}", "Smart TV {brand} {size}\"", 
        "Tablet {brand} {series}", "Digital Camera {brand} {series}",
        "Gaming Console {brand} {series}", "Monitor {brand} {size}\"", 
        "Smart Speaker {brand}", "Smartwatch {brand} {series}",
        "Drone {brand} {series}", "Power Bank {brand} {size}mAh"
    ]
    electronics_brands = ["Samsung", "Apple", "Sony", "LG", "Xiaomi", "Lenovo", "Dell", 
                         "HP", "Canon", "Bose", "JBL", "Philips", "Asus", "Acer"]
    
    # Define clothing templates and brands
    clothing_templates = [
        "{brand} {color} T-shirt", "{brand} {style} Jeans", 
        "{brand} {style} Sneakers", "{brand} {style} Dress in {color}", 
        "{brand} {material} Jacket", "{brand} {color} Hoodie",
        "{brand} {material} Scarf in {color}", "{brand} Cap in {color}", 
        "{brand} {style} Pants", "{brand} {pattern} Socks",
        "{brand} {material} Coat", "{brand} {style} Skirt in {color}"
    ]
    clothing_brands = ["Nike", "Adidas", "Zara", "H&M", "Levi's", "Gap", "Under Armour", 
                      "Puma", "Calvin Klein", "Ralph Lauren", "Tommy Hilfiger", "New Balance"]
    
    # Define home & kitchen templates and brands
    home_templates = [
        "{brand} Non-stick Pan {size}cm", "{brand} {material} Bed Sheet Set", 
        "{brand} {style} Table Lamp", "{brand} {material} Rug {size}m", 
        "{brand} Towel Set {color}", "{brand} {material} Pillow",
        "{brand} {material} Utensil Set", "{brand} {material} Blanket in {color}", 
        "{brand} {material} Planter {size}cm", "{brand} {material} Curtains in {color}",
        "{brand} {style} Wall Clock", "{brand} {material} {style} Organizer"
    ]
    home_brands = ["IKEA", "Tefal", "OXO", "KitchenAid", "Crate & Barrel", "Bed Bath & Beyond", 
                  "Wayfair", "Pyrex", "Corelle", "Bosch", "West Elm", "Pottery Barn"]
    
    # Define beauty templates and brands
    beauty_templates = [
        "{brand} Perfume {scent}", "{brand} Moisturizing Cream", 
        "{brand} {color} Makeup Set", "{brand} Shampoo for {hair_type}", 
        "{brand} Mascara", "{brand} {scent} Essential Oil",
        "{brand} Nail Polish in {color}", "{brand} Foundation", 
        "{brand} Skincare Kit", "{brand} Matte Lipstick in {color}",
        "{brand} {scent} Deodorant", "{brand} Facial Serum"
    ]
    beauty_brands = ["L'Oréal", "Maybelline", "Nivea", "Dove", "Olay", "MAC", "Clinique", 
                    "Estée Lauder", "Neutrogena", "Garnier", "Revlon", "CeraVe"]
    
    # Define sports templates and brands
    sports_templates = [
        "{brand} {color} Yoga Mat", "{brand} Exercise Bike", 
        "{brand} {weight}lb Dumbbell Set", "{brand} Running Shoes {color}", 
        "{brand} Tennis Racket", "{brand} Camping Tent {size}-Person",
        "{brand} {color} Backpack", "{brand} Bicycle Helmet", 
        "{brand} {color} Swimming Goggles", "{brand} Basketball",
        "{brand} Trekking Poles", "{brand} Golf Set"
    ]
    sports_brands = ["Nike", "Adidas", "Under Armour", "Columbia", "The North Face", "Coleman", 
                    "Wilson", "Spalding", "Fitbit", "Schwinn", "Callaway", "Speedo"]
    
    # Additional attributes to personalize products
    colors = ["Black", "White", "Blue", "Red", "Green", "Gray", "Pink", "Purple", "Yellow", "Orange"]
    materials = ["Cotton", "Leather", "Wool", "Silk", "Metal", "Wood", "Plastic", "Ceramic", "Glass"]
    styles = ["Casual", "Elegant", "Athletic", "Vintage", "Modern", "Classic", "Bohemian", "Minimalist"]
    sizes = ["32", "40", "43", "49", "55", "65", "S", "M", "L", "XL", "XXL", "15", "20", "25", "30"]
    series = ["Pro", "Plus", "Max", "Lite", "Ultra", "Air", "Next", "Elite", "Premium", "Basic"]
    patterns = ["Patterned", "Striped", "Solid", "Checkered", "Floral", "Polka Dot", "Geometric"]
    scents = ["Lavender", "Vanilla", "Citrus", "Floral", "Woody", "Spicy", "Fresh"]
    hair_types = ["Dry Hair", "Oily Hair", "Normal Hair", "Colored Hair", "Curly Hair"]
    weights = ["5", "10", "15", "20", "25", "30", "40", "50"]
    
    # Group categories by type for better matching
    electronics_categories = []
    clothing_categories = []
    home_categories = []
    beauty_categories = []
    sports_categories = []
    books_categories = []
    toys_categories = []
    automotive_categories = []
    health_categories = []
    jewelry_categories = []
    other_categories = []
    
    # Create a mapping from category_id to main parent category
    category_to_parent_mapping = {}
    
    # Organize category IDs by type and build parent mapping
    for category_id in category_ids:
        category_name = category_mapping.get(category_id, "")
        
        # Find the parent category for this category
        parent_category = "Other"
        for main_cat in main_category_names:
            if main_cat in category_name:
                parent_category = main_cat
                break
                
        # Store the parent category mapping
        category_to_parent_mapping[category_id] = parent_category
        
        # Categorize based on parent category
        if parent_category == "Electronics":
            electronics_categories.append(category_id)
        elif parent_category == "Clothing":
            clothing_categories.append(category_id)
        elif parent_category == "Home & Kitchen":
            home_categories.append(category_id)
        elif parent_category == "Beauty & Personal Care":
            beauty_categories.append(category_id)
        elif parent_category == "Sports & Outdoors":
            sports_categories.append(category_id)
        elif parent_category == "Books":
            books_categories.append(category_id)
        elif parent_category == "Toys & Games":
            toys_categories.append(category_id)
        elif parent_category == "Automotive":
            automotive_categories.append(category_id)
        elif parent_category == "Health & Wellness":
            health_categories.append(category_id)
        elif parent_category == "Jewelry":
            jewelry_categories.append(category_id)
        else:
            other_categories.append(category_id)
    
    # Ensure we have at least one category of each type by using other categories as fallback
    all_category_lists = [
        electronics_categories, clothing_categories, home_categories,
        beauty_categories, sports_categories, books_categories,
        toys_categories, automotive_categories, health_categories,
        jewelry_categories
    ]
    
    for i, category_list in enumerate(all_category_lists):
        if not category_list:
            all_category_lists[i] = other_categories if other_categories else category_ids
    
    with open('Products.csv', 'w', newline='', encoding='utf-8') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for product_id in range(1, num_products + 1):
            if product_id % 100 == 0:
                print(f'{product_id}', end=' ', flush=True)
            
            # First select a parent category
            parent_category_name = random.choice(main_category_names)
            
            # Choose appropriate category lists based on parent category
            if parent_category_name == "Electronics":
                category_list = electronics_categories
                template_list = electronics_templates
                brand_list = electronics_brands
            elif parent_category_name == "Clothing":
                category_list = clothing_categories
                template_list = clothing_templates
                brand_list = clothing_brands
            elif parent_category_name == "Home & Kitchen":
                category_list = home_categories
                template_list = home_templates
                brand_list = home_brands
            elif parent_category_name == "Beauty & Personal Care":
                category_list = beauty_categories
                template_list = beauty_templates
                brand_list = beauty_brands
            elif parent_category_name == "Sports & Outdoors":
                category_list = sports_categories
                template_list = sports_templates
                brand_list = sports_brands
            elif parent_category_name == "Books":
                category_list = books_categories
                template_list = ["{brand} {adjective} {category} Book"]
                brand_list = ["Penguin", "Harper", "Oxford", "Random House", "Simon & Schuster", "Vintage"]
            elif parent_category_name == "Toys & Games":
                category_list = toys_categories
                template_list = ["{brand} {adjective} {category} Toy", "{brand} {category} Game Set"]
                brand_list = ["LEGO", "Hasbro", "Mattel", "Fisher-Price", "Playmobil", "Melissa & Doug"]
            elif parent_category_name == "Automotive":
                category_list = automotive_categories
                template_list = ["{brand} {category} {adjective} Accessory", "{brand} Car {category}"]
                brand_list = ["Bosch", "3M", "Meguiar's", "Michelin", "Shell", "Castrol"]
            elif parent_category_name == "Health & Wellness":
                category_list = health_categories
                template_list = ["{brand} {category} {adjective} Supplement", "{brand} {category} Aid"]
                brand_list = ["Nature's Way", "GNC", "Centrum", "Nordic Naturals", "NOW Foods", "Garden of Life"]
            elif parent_category_name == "Jewelry":
                category_list = jewelry_categories
                template_list = ["{brand} {material} {category}", "{brand} {style} {category} with {material}"]
                brand_list = ["Tiffany", "Pandora", "Swarovski", "Cartier", "Kay", "Alex and Ani"]
            else:
                category_list = other_categories
                template_list = ["{brand} {category} Item"]
                brand_list = ["Generic", "Quality", "Premium", "Standard", "Best", "Elite"]
            
            # If the selected category list is empty, fall back to other categories
            if not category_list:
                category_list = other_categories if other_categories else category_ids
                
            # Now select a specific category ID from the appropriate list
            category_id = random.choice(category_list)
            
            category_name = category_mapping.get(category_id, "")
            
            # Select a template and fill it with attributes
            template = random.choice(template_list)
            
            # Additional attributes for new templates
            adjectives = ["Fantastic", "Premium", "Deluxe", "Professional", "Essential", "Luxury", "Classic", "Advanced"]
            rooms = ["Living Room", "Bedroom", "Office", "Kitchen", "Bathroom", "Dining Room", "Patio"]
            
            # Get the specific category name
            category_name = category_mapping.get(category_id, "Product")
            
            try:
                # Prepare all possible format parameters
                format_params = {
                    "brand": random.choice(brand_list),
                    "color": random.choice(colors),
                    "material": random.choice(materials),
                    "style": random.choice(styles),
                    "size": random.choice(sizes),
                    "series": random.choice(series),
                    "pattern": random.choice(patterns),
                    "scent": random.choice(scents),
                    "hair_type": random.choice(hair_types),
                    "weight": random.choice(weights),
                    "category": category_name,
                    "adjective": random.choice(adjectives),
                    "room": random.choice(rooms)
                }
                
                # Generate product name using template
                name = template.format(**format_params)
            except KeyError:
                # If the template has placeholders we don't have values for, use a simpler approach
                name = f"{random.choice(brand_list)} {category_name}"
            
            # Ensure the name is not repeated
            counter = 1
            original_name = name
            while name in used_names:
                name = f"{original_name} ({counter})"
                counter += 1
            
            used_names.add(name)
            
            # Generate a realistic description based on the product name and category
            description = generate_product_description(name, category_name)

            # We already know the parent category name from selection above
            # Set the image name based on the parent category
            image = f"{parent_category_name.replace(' & ', '_').replace(' ', '_')}.jpg"

            creator_id = random.choice(seller_ids)
            
            products.append((product_id, name, creator_id))
            
            writer.writerow([
                product_id,
                name,
                description,
                image,
                category_id,
                creator_id
            ])
        print(f'{num_products} generated')
    return products

def gen_inventory(num_inventory_items, products, seller_ids):
    """Generate Inventory table"""
    with open('Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Inventory...', end=' ', flush=True)
        
        # Track existing seller-product combinations to avoid duplicates
        existing_inventory = set()
        
        for item_id in range(1, num_inventory_items + 1):
            if item_id % 100 == 0:
                print(f'{item_id}', end=' ', flush=True)
            
            product_id, _, creator_id = random.choice(products)
            
            # For 70% of entries, use the creator as the seller
            # For 30%, use a different random seller
            if random.random() < 0.7:
                seller_id = creator_id
            else:
                seller_id = random.choice(seller_ids)
            
            # Skip if this seller-product combination already exists
            if (seller_id, product_id) in existing_inventory:
                continue
            
            existing_inventory.add((seller_id, product_id))
            
            price = round_decimal(str(random.uniform(5, 500)))
            quantity = random.randint(0, 1000)
            created_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                item_id,
                seller_id,
                product_id,
                price,
                quantity,
                created_at,
                'published',   # publish_status，by default ---jiechen
                50             # low_stock_quantity，by default ---jiechen
            ])
        print(f'{len(existing_inventory)} generated')
    return existing_inventory

def gen_purchases(num_purchases, user_ids):
    """Generate Purchases table"""
    purchase_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    with open('Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        
        purchases = []
        for purchase_id in range(1, num_purchases + 1):
            if purchase_id % 100 == 0:
                print(f'{purchase_id}', end=' ', flush=True)
            
            user_id = random.choice(user_ids)
            total_items = random.randint(1, 10)
            total_amount = round_decimal(str(random.uniform(total_items * 5, total_items * 100)))
            status = random.choice(purchase_statuses)
            updated_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            purchases.append((purchase_id, user_id, total_amount, status, updated_at))
            
            writer.writerow([
                purchase_id,
                user_id,
                total_amount,
                total_items,
                status,
                updated_at
            ])
        print(f'{num_purchases} generated')
    return purchases

def gen_purchase_items(num_purchase_items, purchases, inventory):
    """Generate Purchase Items table"""
    fulfillment_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    with open('Purchase_items.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchase Items...', end=' ', flush=True)
        
        purchase_items = []
        for purchase_item_id in range(1, num_purchase_items + 1):
            if purchase_item_id % 100 == 0:
                print(f'{purchase_item_id}', end=' ', flush=True)
            
            # Select a random purchase
            purchase_id, user_id, _, purchase_status, _ = random.choice(purchases)
            
            # Select a random inventory item
            if not inventory:
                continue
            
            seller_id, product_id = random.choice(list(inventory))
            
            quantity = random.randint(1, 5)
            unit_price = round_decimal(str(random.uniform(5, 200)))
            total_price = round_decimal(str(float(unit_price) * quantity))
            
            # Set fulfillment status based on purchase status
            if purchase_status == 'cancelled':
                fulfillment_status = 'cancelled'
            elif purchase_status == 'delivered':
                fulfillment_status = 'delivered'
            else:
                fulfillment_status = random.choice(fulfillment_statuses[:3])  # Only pending, processing, shipped
            
            updated_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            purchase_items.append((purchase_item_id, purchase_id, product_id, seller_id, quantity, unit_price, total_price))
            
            writer.writerow([
                purchase_item_id,
                purchase_id,
                product_id,
                seller_id,
                quantity,
                unit_price,
                total_price,
                fulfillment_status,
                updated_at
            ])
        print(f'{num_purchase_items} generated')
    return purchase_items

def gen_seller_purchases(num_seller_purchases, purchases, seller_ids):
    """Generate Seller Purchases table"""
    with open('Seller_purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Seller Purchases...', end=' ', flush=True)
        
        seller_purchases = []
        for seller_purchase_id in range(1, num_seller_purchases + 1):
            if seller_purchase_id % 100 == 0:
                print(f'{seller_purchase_id}', end=' ', flush=True)
            
            purchase_id, user_id, _, purchase_status, updated_at = random.choice(purchases)
            seller_id = random.choice(seller_ids)
            
            total_items = random.randint(1, 5)
            total_amount = round_decimal(str(random.uniform(total_items * 5, total_items * 100)))
            
            seller_purchases.append((seller_purchase_id, purchase_id, seller_id))
            
            writer.writerow([
                seller_purchase_id,
                user_id,
                seller_id,
                purchase_id,
                total_amount,
                total_items,
                purchase_status,  # Use the same status as the original purchase
                updated_at
            ])
        print(f'{num_seller_purchases} generated')
    return seller_purchases

def gen_seller_purchase_items(num_items, seller_purchases, products):
    """Generate Seller Purchase Items table"""
    fulfillment_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    with open('Seller_purchase_items.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Seller Purchase Items...', end=' ', flush=True)
        
        for item_id in range(1, num_items + 1):
            if item_id % 100 == 0:
                print(f'{item_id}', end=' ', flush=True)
            
            seller_purchase_id, _, seller_id = random.choice(seller_purchases)
            
            # Filter products by this seller
            seller_products = [p for p in products if p[2] == seller_id]
            if not seller_products:
                product_id, _, _ = random.choice(products)
            else:
                product_id, _, _ = random.choice(seller_products)
            
            quantity = random.randint(1, 5)
            unit_price = round_decimal(str(random.uniform(5, 200)))
            total_price = round_decimal(str(float(unit_price) * quantity))
            fulfillment_status = random.choice(fulfillment_statuses)
            updated_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                item_id,
                seller_purchase_id,
                product_id,
                quantity,
                unit_price,
                total_price,
                fulfillment_status,
                updated_at
            ])
        print(f'{num_items} generated')

def gen_cart(num_cart, user_ids):
    """Generate Cart table"""
    with open('Cart.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Carts...', end=' ', flush=True)
        
        # Track which users already have carts
        used_user_ids = set()
        carts = []
        cart_id = 1
        
        # Make sure we don't try to create more carts than users
        num_cart = min(num_cart, len(user_ids))
        
        while cart_id <= num_cart:
            if cart_id % 50 == 0:
                print(f'{cart_id}', end=' ', flush=True)
            
            # Select a user_id that hasn't been used yet
            available_user_ids = [uid for uid in user_ids if uid not in used_user_ids]
            if not available_user_ids:
                print("Warning: No more unused user IDs available for carts")
                break
                
            user_id = random.choice(available_user_ids)
            used_user_ids.add(user_id)
            
            updated_at = fake.date_time_between(start_date='-30d', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            carts.append((cart_id, user_id))
            
            writer.writerow([
                cart_id,
                user_id,
                updated_at
            ])
            cart_id += 1
            
        print(f'{len(carts)} generated')
    return carts

def gen_cart_items(num_cart_items, carts, inventory):
    """Generate Cart Items table"""
    with open('Cart_items.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Cart Items...', end=' ', flush=True)
        
        for cart_item_id in range(1, num_cart_items + 1):
            if cart_item_id % 50 == 0:
                print(f'{cart_item_id}', end=' ', flush=True)
            
            cart_id, _ = random.choice(carts)
            
            if not inventory:
                continue
                
            seller_id, product_id = random.choice(list(inventory))
            
            quantity = random.randint(1, 5)
            unit_price = round_decimal(str(random.uniform(5, 200)))
            total_price = round_decimal(str(float(unit_price) * quantity))
            
            writer.writerow([
                cart_item_id,
                cart_id,
                product_id,
                seller_id,
                quantity,
                unit_price,
                total_price
            ])
        print(f'{num_cart_items} generated')

def generate_product_review(rating):
    """Generate a realistic product review based on rating (1-5)"""
    
    # Define review templates by rating
    review_templates = {
        # 5-star reviews (very positive)
        5: [
            "Absolutely love this product! The quality is outstanding and it exceeded all my expectations. Definitely worth every penny!",
            "This product is a game-changer! The quality is exceptional and exactly what I needed. Highly recommend to anyone!",
            "Wow! This product has completely exceeded my expectations. Incredibly well-made, works perfectly, and the customer service was excellent.",
            "Perfect product for anyone looking for quality and value. Easy to use, works flawlessly, and has all the features I was looking for. Best purchase I've made this year!",
            "This is everything it promised to be and more! Exceptional quality and beautifully designed. Could not be happier with this purchase."
        ],
        
        # 4-star reviews (mostly positive with minor issues)
        4: [
            "Really happy with this product. The quality is great and it has almost all the features I was looking for. Overall, a great purchase!",
            "Very good product! The build quality is impressive and it works well for my needs. Missing one feature I was hoping for, but otherwise excellent.",
            "Very satisfied with this purchase. It's reliable, well-designed, and offers good performance for the price. One minor issue keeps it from being perfect.",
            "Great product with impressive features. The quality feels premium and it works exactly as described. Only a few small details could be improved.",
            "Definitely worth buying. The performance is consistent and the design is thoughtful. Has all the core features I needed and works reliably."
        ],
        
        # 3-star reviews (mixed feelings)
        3: [
            "Decent product that does the job. Nothing extraordinary but no major issues either. Fair value for the price I paid.",
            "It's okay. Some aspects are well done while others could use improvement. It serves its purpose but doesn't exceed expectations.",
            "Middle-of-the-road product. Has some good features but also some drawbacks. Meets basic needs but nothing exceptional about it.",
            "Satisfactory purchase. Works as advertised but the quality could be better. Not disappointed but not impressed either.",
            "Average quality product. It functions adequately but doesn't stand out in any particular way. Gets the job done but that's about it."
        ],
        
        # 2-star reviews (mostly negative with some positive aspects)
        2: [
            "Disappointed with this purchase. The quality is below what I expected and it doesn't work very well. A few good features but overall not worth the money.",
            "This product has too many issues to recommend. Doesn't perform as advertised and the quality feels cheap. The only positive is the customer service.",
            "Not happy with this product. It partially works but is frustrating to use. Had higher expectations based on the description and price.",
            "Below average product with some design flaws. Works occasionally but not consistently. Wouldn't purchase again or recommend to others.",
            "Expected much better for the price. Poor quality materials and inconsistent performance. The design is nice but doesn't make up for the problems."
        ],
        
        # 1-star reviews (very negative)
        1: [
            "Complete waste of money. Barely functions as advertised and the quality is terrible. Avoid this product!",
            "Extremely disappointed. The product arrived damaged and doesn't work properly. Customer service was unhelpful when I tried to resolve the issue.",
            "Do not buy this product. It broke after minimal use and the quality is much lower than depicted. Save your money and look elsewhere.",
            "Terrible experience with this product. Doesn't work as described, poor quality, and not worth even a fraction of the price.",
            "Regret this purchase entirely. The product is defective, poorly designed, and completely fails to perform its basic function. Stay away!"
        ]
    }
    
    # Select a random review template based on the rating
    import random
    templates = review_templates.get(rating, review_templates[3])  # Default to 3-star if invalid rating
    return random.choice(templates)


def gen_product_reviews(num_reviews, products, user_ids):
    """Generate Product Reviews table with realistic reviews"""
    with open('Product_reviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Product Reviews...', end=' ', flush=True)
        
        for review_id in range(1, num_reviews + 1):
            if review_id % 50 == 0:
                print(f'{review_id}', end=' ', flush=True)
            
            product_id, _, _ = random.choice(products)
            user_id = random.choice(user_ids)
            
            # Generate a rating with a bias toward higher ratings (more realistic)
            # 5-star: 40%, 4-star: 30%, 3-star: 15%, 2-star: 10%, 1-star: 5%
            rating_weights = [0.05, 0.10, 0.15, 0.30, 0.40]
            rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]
            
            # Generate a realistic review based on the rating
            review_text = generate_product_review(rating)
            
            updated_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                review_id,
                user_id,
                product_id,
                review_text,
                rating,
                updated_at
            ])
        print(f'{num_reviews} generated')

def gen_seller_reviews(num_reviews, seller_ids, user_ids):
    """Generate Seller Reviews table with realistic reviews"""
    with open('Seller_reviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Seller Reviews...', end=' ', flush=True)
        
        # Define seller-specific review templates
        seller_review_templates = {
            5: [
                "Outstanding seller! Fast shipping, excellent communication, and the product was exactly as described. Would definitely buy from them again!",
                "Five-star experience with this seller. Package arrived ahead of schedule and was perfectly packaged. Great customer service when I had questions.",
                "Excellent seller to deal with. Very professional, quick responses to my inquiries, and the item arrived in perfect condition. Highly recommend!",
                "Best online shopping experience I've had. The seller was incredibly helpful, shipping was fast, and the product exceeded my expectations.",
                "Amazing seller! They went above and beyond to make sure I was satisfied with my purchase. Fast shipping and product exactly as advertised."
            ],
            4: [
                "Good seller with fast shipping and reliable service. The product was as described and arrived on time. Would shop with them again.",
                "Very positive experience with this seller. Communication was good and the product arrived in good condition. Shipping took a bit longer than expected.",
                "Reliable seller with quality products. The item was well-packaged and as described. Only minor issue was a slight delay in shipping.",
                "Good experience overall. The seller was responsive, the item was as pictured, and shipping was reasonable. Would recommend with minor reservations.",
                "Satisfied with this purchase. The seller was professional and the product matched the description. A small packaging issue prevents a 5-star rating."
            ],
            3: [
                "Average experience with this seller. Product was okay and arrived within the expected timeframe. Nothing exceptional but no major issues either.",
                "Decent seller. The item arrived and works as expected, but communication could have been better when I had questions about shipping.",
                "Neutral experience. The product meets basic expectations but the shipping took longer than indicated. Seller was responsive when contacted.",
                "Satisfactory transaction. The item is as described but the packaging could have been better. Delivery was within the estimated timeframe.",
                "Middle-of-the-road experience. Product quality is acceptable but not exceptional. Seller responds to messages but not very quickly."
            ],
            2: [
                "Disappointed with this seller. Slow shipping and the product wasn't exactly as described. Customer service was slow to respond to my concerns.",
                "Below average experience. The product eventually arrived but was delayed without explanation. Quality wasn't what I expected based on the listing.",
                "Not a great experience. Communication was poor and the item arrived later than promised. Product quality was also less than expected.",
                "Wouldn't recommend this seller. Shipping issues, packaging was insufficient, and the product had minor damage. Difficult to get assistance.",
                "Frustrating experience with this seller. Delayed shipping with no updates, and the product didn't fully match the description. Poor communication."
            ],
            1: [
                "Terrible experience! The product never arrived and the seller was unresponsive to my messages. Had to file for a refund.",
                "Avoid this seller. The item arrived damaged and completely unusable. Customer service refused to help resolve the issue.",
                "Worst online shopping experience ever. Wrong item shipped, seller refused to correct the mistake, and was rude in communications.",
                "Do not buy from this seller! Product was clearly misrepresented in the listing, arrived very late, and was damaged. No response to complaints.",
                "Extremely poor service. Item was significantly delayed, poorly packaged, and damaged upon arrival. Seller ignored all attempts to resolve the issue."
            ]
        }
        
        for review_id in range(1, num_reviews + 1):
            if review_id % 50 == 0:
                print(f'{review_id}', end=' ', flush=True)
            
            seller_id = random.choice(seller_ids)
            user_id = random.choice(user_ids)
            
            # Generate a rating with a bias toward higher ratings
            rating_weights = [0.05, 0.10, 0.15, 0.30, 0.40]
            rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]
            
            # Select a random seller review template based on the rating
            templates = seller_review_templates.get(rating, seller_review_templates[3])
            review_text = random.choice(templates)
            
            updated_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                review_id,
                seller_id,
                user_id,
                review_text,
                rating,
                updated_at
            ])
        print(f'{num_reviews} generated')

def gen_account_transactions(num_transactions, accounts, purchases):
    """Generate Account Transactions table"""
    transaction_types = ['purchase', 'refund', 'deposit', 'withdrawal']
    
    with open('Account_transactions.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Account Transactions...', end=' ', flush=True)
        
        for transaction_id in range(1, num_transactions + 1):
            if transaction_id % 100 == 0:
                print(f'{transaction_id}', end=' ', flush=True)
            
            account_id = random.choice(accounts)
            transaction_type = random.choice(transaction_types)
            
            # Link to purchase or set to empty based on transaction type
            purchase_id = None
            if transaction_type in ['purchase', 'refund']:
                purchase_id = random.choice([p[0] for p in purchases])
            
            # Amount based on transaction type
            if transaction_type == 'purchase':
                amount = round_decimal(str(-1 * random.uniform(10, 500)))
            elif transaction_type == 'refund':
                amount = round_decimal(str(random.uniform(10, 500)))
            elif transaction_type == 'deposit':
                amount = round_decimal(str(random.uniform(50, 1000)))
            else:  # withdrawal
                amount = round_decimal(str(-1 * random.uniform(50, 500)))
            
            created_at = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                transaction_id,
                purchase_id if purchase_id is not None else '',
                account_id,
                amount,
                transaction_type,
                created_at
            ])
        print(f'{num_transactions} generated')

def gen_coupons(num_coupons=20):
    """Generate Coupons table"""
    print('Generating Coupons...')
    
    with open('Coupons.csv', 'w') as f: 
        writer = get_csv_writer(f)
        
        # Generate fixed codes for testing plus random ones
        fixed_codes = [
            ('WELCOME10', 10.00),
            ('SALE20', 20.00),
            ('SPECIAL25', 25.00),
            ('HOLIDAY30', 30.00),
            ('FLASH50', 50.00)
        ]
        
        coupon_id = 1
        
        # Write fixed codes first
        for code, discount in fixed_codes:
            valid_from = fake.date_time_between(start_date='-30d', end_date='-15d').strftime('%Y-%m-%d %H:%M:%S')
            valid_until = fake.date_time_between(start_date='+15d', end_date='+60d').strftime('%Y-%m-%d %H:%M:%S')
            
            writer.writerow([
                coupon_id,
                code,
                discount,
                valid_from,
                valid_until,
                True  # is_active
            ])
            coupon_id += 1
        
        # Generate random coupons for the rest
        for i in range(coupon_id, num_coupons + 1):
            code = fake.bothify(text='???##??').upper()
            discount_percent = round(random.uniform(5.0, 40.0), 2)
            valid_from = fake.date_time_between(start_date='-60d', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            
            # 70% chance of valid coupon, 30% chance of expired
            if random.random() < 0.7:
                valid_until = fake.date_time_between(start_date='+1d', end_date='+90d').strftime('%Y-%m-%d %H:%M:%S')
                is_active = True
            else:
                valid_until = fake.date_time_between(start_date='-30d', end_date='-1d').strftime('%Y-%m-%d %H:%M:%S')
                is_active = random.choice([True, False])
            
            writer.writerow([
                i,
                code,
                discount_percent,
                valid_from,
                valid_until,
                is_active
            ])


# Generate tables in proper order
# Generate base tables first
user_ids = gen_users(num_users)
seller_ids = gen_sellers(num_sellers)
account_ids = gen_accounts(num_accounts, user_ids, seller_ids)
category_ids, category_mapping = gen_categories(num_categories)
products = gen_products(num_products, category_ids, category_mapping, seller_ids)

# Generate related tables
inventory = gen_inventory(num_inventory_items, products, seller_ids)
purchases = gen_purchases(num_purchases, user_ids)
purchase_items = gen_purchase_items(num_purchase_items, purchases, inventory)
seller_purchases = gen_seller_purchases(num_seller_purchases, purchases, seller_ids)
gen_seller_purchase_items(num_seller_purchase_items, seller_purchases, products)

# Generate carts
carts = gen_cart(num_cart, user_ids)
gen_cart_items(num_cart_items, carts, inventory)

# Generate reviews
gen_product_reviews(num_product_reviews, products, user_ids)
gen_seller_reviews(num_seller_reviews, seller_ids, user_ids)

# Generate transactions
gen_account_transactions(num_account_transactions, account_ids, purchases)

gen_coupons()