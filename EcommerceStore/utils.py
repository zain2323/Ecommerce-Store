from pathlib import Path
import secrets
from PIL import Image
from EcommerceStore.models import Category, Variant
from EcommerceStore import db
from datetime import datetime

class UtilityFunctions:

    @staticmethod
    def save_picture(image_data, img_name):
        '''
        This saves the thumbnail picture of the product in the static/product_pictures directory.
        Picture is being renamed  to the randomly chosen 32 bit string in order to avoid the
        naming clash.
        '''
        try:
            path = Path('./EcommerceStore/static/product_images')
        except FileNotFoundError:
            raise FileNotFoundError("Path is invalid or does not exist.")
        try:
            _, ext = image_data.filename.split(".")
        except:
            ext = image_data.filename.split(".")[-1]
        image_name_with_ext = img_name + "." + ext
        path = path.joinpath(image_name_with_ext)
        try:
            i = Image.open(image_data)
        except FileNotFoundError:
            raise Exception(f"File {image_data} not found at the given path.")
        i = i.resize((500,375))
        i.save(path)
        return image_name_with_ext
    
    @staticmethod
    def delete_picture(img_name):
        try:
            path = Path("./EcommerceStore/static/product_images/" + img_name)
        except FileNotFoundError:
            raise FileNotFoundError("Path is invalid or does not exist.")
        if path.exists():
            path.unlink()
        else:
            raise FileNotFoundError("File with the given name do not exists.")

    @staticmethod
    def get_total_amount(buyer_cart_list):
        '''
        Returns the total amount of all the products user has added in the card.
        This is does not include delivery charges.
        '''
        if type(list(buyer_cart_list)) is not list:
            raise TypeError("Parameter buyer_cart_list must be of list type.")
        amount = 0
        try:
            for buyer_cart in buyer_cart_list:
                product_cost = buyer_cart.product.product_variants[0].price * buyer_cart.quantity
                amount += product_cost
            return round(float(amount), 2)
        except AttributeError:
            raise AttributeError("Elements of the passed parameter must be of type BuyerCart")
    
    @staticmethod
    def get_parent_categories():
        '''
        Returns all the parent categories.
        parent_id is equal to the id attribute of parent.
        '''
        categories = Category.query.all()
        parent_categories = []
        for parent in categories:
            if parent.id == parent.parent_id:
                parent_categories.append(parent)
        return parent_categories
    
    @staticmethod
    def set_parent_category(category_name):
        '''
        Sets the parent_id attribute of the fetched category to the id attribute of itself.
        '''
        if type(category_name) is not str:
            raise TypeError("parameter category_name must be of str type.")
        category = Category.query.filter_by(category=category_name).first()
        category_id = category.id
        category.parent_id = category_id
        db.session.commit()
    
    @staticmethod
    def save_template(template, template_name):
        '''
        Saves the template in the static/invoice directory
        '''
        try:
            path = Path('./EcommerceStore/static/invoices').joinpath(template_name)
            with path.open(mode="w") as file:
                file.write(template)
        except FileNotFoundError:
            raise FileNotFoundError("File with the given name does not exists.")
    
    @staticmethod
    def generate_hex_name():
        '''
        Returns the 32 bit random digits
        '''
        return secrets.token_hex(32)
    
    @staticmethod
    def get_utctime():
        '''n
        Returns the current UTC time
        '''
        return datetime.utcnow()
    
    @staticmethod
    def get_categories():
        categories = Category.query.all()
        return categories
  
    @staticmethod
    def get_variants():
        variants = Variant.query.all()
        return variants
    
    @staticmethod
    def get_seller_entry(seller, product_id):
        '''
        Fetches the seller entry in the SellerProducts table
        with respect to the product id and returns that entry.
        In another case returns None.
        '''
        try:
            entries = seller.seller_products
            for entry in entries:
                if entry.product_id == product_id:
                    return entry
        except AttributeError:
            AttributeError("You must pass User type object.")
        return None