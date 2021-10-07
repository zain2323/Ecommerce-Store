from abc import ABC, abstractmethod

class Variant(ABC):

    @abstractmethod
    def get_id():
        pass
    
    @abstractmethod
    def get_variant_name():
        pass

    @abstractmethod    
    def __repr__():
        pass

class Category(ABC):

    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_parent_id():
        pass

    @abstractmethod
    def get_category():
        pass

    @abstractmethod    
    def __repr__():
        pass

class Product(ABC):

    @abstractmethod
    def get_id():
        pass
    
    @abstractmethod
    def get_category_id():
        pass
    
    @abstractmethod
    def get_variant_id():
        pass
    
    @abstractmethod
    def get_name():
        pass
    
    @abstractmethod
    def get_keywords():
        pass
     
    @abstractmethod
    def get_manufacturer():
        pass

    @abstractmethod
    def get_sales():
        pass

    @abstractmethod
    def get_review_count():
        pass

    @abstractmethod    
    def __repr__():
        pass

class User(ABC):

    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_name():
        pass

    @abstractmethod
    def get_username():
        pass

    @abstractmethod
    def get_email():
        pass

    @abstractmethod
    def get_password():
        pass

    @abstractmethod
    def get_role():
        pass

    @abstractmethod
    def get_registered_at():
        pass

    @abstractmethod
    def get_confirmed():
        pass

    @abstractmethod
    def get_province():
        pass

    @abstractmethod
    def get_city():
        pass

    @abstractmethod
    def get_address():
        pass

    @abstractmethod    
    def __repr__():
        pass

class SoldProducts(ABC):

    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_buyer_id():
        pass

    @abstractmethod
    def get_invoice():
        pass

    @abstractmethod    
    def __repr__():
        pass

class Store(ABC):

    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_name():
        pass

    @abstractmethod
    def get_seller_id():
        pass

    @abstractmethod    
    def __repr__():
        pass

class SellerProducts(ABC):

    @abstractmethod
    def get_id():
        pass
    
    @abstractmethod
    def get_product_id():
        pass

    @abstractmethod
    def get_seller_id():
        pass

    @abstractmethod    
    def __repr__():
        pass

class ProductVariants(ABC):

    @abstractmethod
    def get_id():
        pass
    
    @abstractmethod
    def get_product_id():
        pass
    
    @abstractmethod
    def get_seller_id():
        pass
    
    @abstractmethod
    def get_variant_id():
        pass
    
    @abstractmethod
    def get_value():
        pass
    
    @abstractmethod
    def get_sku():
        pass
    
    @abstractmethod
    def get_price():
        pass
    
    @abstractmethod
    def get_stock():
        pass
    
    @abstractmethod
    def get_desc():
        pass
    
    @abstractmethod
    def get_thumbnail_img():
        pass

    @abstractmethod    
    def __repr__():
        pass
    
class Cart(ABC):
    
    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_buyer_id():
        pass

    @abstractmethod    
    def __repr__():
        pass 

class BuyerCart(ABC):

    @abstractmethod
    def get_id():
        pass

    @abstractmethod
    def get_cart_id():
        pass

    @abstractmethod
    def get_product_id():
        pass

    @abstractmethod
    def get_quantity():
        pass

    @abstractmethod    
    def __repr__():
        pass 