from datetime import datetime
from flask_login.mixins import UserMixin
from sqlalchemy.orm import backref
from EcommerceStore import db, login_manager, create_app
from datetime import datetime

class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_name = db.Column(db.String(30), nullable=False, unique=True)
    products = db.relationship("Product", backref='variant', lazy=True)

    def __repr__(self):
        return f"{self.variant_name}"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='RESTRICT'))
    category = db.Column(db.String(30), nullable=False, unique=True)
    parent_category = db.relationship("Category", backref=backref('parent', remote_side=[id]))
    products = db.relationship("Product", backref='category', lazy=True)

    def __repr__(self):
        return f"{self.category}"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='RESTRICT'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.id', ondelete='RESTRICT'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    keywords = db.Column(db.String, nullable=False)
    manufacturer = db.Column(db.String(30), nullable=False)
    sales = db.Column(db.Integer, default=0, nullable=False)
    review_count = db.Column(db.Integer, default=0, nullable=False)
    product_variants = db.relationship("ProductVariants", cascade="all, delete",  backref="product", lazy=True)
    seller_products = db.relationship('SellerProducts', cascade="all, delete", backref=db.backref('product',cascade="all, delete"), lazy=True)
    cart = db.relationship("BuyerCart", cascade="all, delete", backref="product", lazy=True)
    
    def __repr__(self):
        return f"Product: {self.name} Brand: {self.manufacturer}"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), default='buyer', nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    province = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    seller_products = db.relationship('SellerProducts', cascade="all, delete", backref='seller', lazy=True)
    sold_products = db.relationship("SoldProducts", cascade="all, delete", backref='buyer', lazy=True)
    seller_store = db.relationship("Store", cascade="all, delete", backref="seller", lazy=True)
    cart = db.relationship("Cart", cascade="all, delete", backref="buyer", lazy=True)
    
    def __repr__(self):
        return f"Name: {self.name} Username: {self.username} Email: {self.email} Role: {self.role}"

class SoldProducts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    purchased_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    invoice = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return f"Buyer: {self.buyer_id} invoice: {self.invoice}"

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"Name: {self.name}"

class SellerProducts(db.Model):
    table_args = (
        db.UniqueConstraint('product_id', 'seller_id', name="unique_product_seller"),
    )
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"ProductId: {self.product_id} SellerID: {self.seller_id}"

class ProductVariants(db.Model):
    table_args = (
        db.UniqueConstraint("product_id", "variant_id", "seller_id", "value"),
    )
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.id', ondelete='RESTRICT'))
    value = db.Column(db.String(30), nullable=False)
    sku = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Numeric, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    desc = db.Column(db.Text, nullable=False)
    thumbnail_img = db.Column(db.String(32), nullable=False)
    
    def __repr__(self):
        return f"ProductVariant: {self.value} SKU: {self.sku} Price: {self.price} Stock: {self.stock}"

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    buyer_cart = db.relationship("BuyerCart", cascade="all, delete", backref="cart", lazy=True)

    def __repr__(self):
        return f"Buyer Id: {self.buyer_id}"
        
class BuyerCart(db.Model):
    table_args = (
        db.UniqueConstraint("cart_id", "product_id"),
        )
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("cart.id", ondelete='CASCADE'))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    
    def __repr__(self):
        return f"cart id: {self.cart_id} product id: {self.product_id} quantity: {self.quantity}"

